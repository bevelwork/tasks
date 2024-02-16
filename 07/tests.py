import pytest

from itertools import chain
from pprint import pprint
from random import choice, uniform

from stratus.common.helpers import asserts_codes, get_random_string, validate_schema, printer, values_exist, \
    print_success, print_pink
from stratus.features.accounts_view.helpers import post_request_body


class TestRequests:

    @pytest.mark.child
    def test_post_request(self, accounts_fixture, storage):
        if accounts_fixture.api.env_data.primary_role == 1:  # DEMO
            pytest.skip('not applicable for parent for the demo')
        dashboard = accounts_fixture.get_dashboard()
        asserts_codes(dashboard, 200)

        account = choice(accounts_fixture.accounts)
        response, body = accounts_fixture.create_request(account['accountId'])
        storage.request = response.json()

        resp = response.json()
        assert resp['status'] == 'pending' and print_success('status: pending')
        assert resp['amount'] == body['amount'] and print_success('amounts match')
        assert resp['requestNote'] == body['note'] and print_success('request notes match')
        assert resp['depositAccount']['accountId'] == body['depositAccountId'] and print_success('deposit accounts match')

        for prep, user_id in [('By', accounts_fixture.primary_user_id), ('From', accounts_fixture.secondary_user_id)]:
            assert resp[f'requested{prep}User']['userId'] == user_id and print_success(f'requested{prep}User - userId is correct')

        validate_schema('request.json', response)
        values_exist(resp, 'responseNote')

    def test_get_request(self, accounts_fixture, storage):
        if accounts_fixture.request_id is None:
            dashboard = accounts_fixture.get_dashboard()
            asserts_codes(dashboard, 200)

            if accounts_fixture.api.env_data.primary_role == 1:
                requests_list = list(
                    chain.from_iterable((x['sentRequests'] for x in dashboard.json()['dashboard']['children'])))
            else:
                requests_list = dashboard.json()['dashboard']['sentRequests']

            if requests_list:
                request = choice(requests_list)
                request_id = request['requestId']
                printer('Request selected from existing ones')
            else:
                if accounts_fixture.api.env_data.primary_role == 1:  # parent is not allowed to make requests for the demo
                    print_pink('Logging in as the child to create request...')
                    child_dash = accounts_fixture.api.secondary.get_dashboard()
                    asserts_codes(child_dash, 200)

                    account = choice(child_dash.json()['dashboard']['accounts'])
                    body = post_request_body(accounts_fixture.primary_user_id, account['accountId'])

                    printer('Creating request as the secondary user...')
                    post_request = accounts_fixture.api.secondary.post_requests(body)
                    asserts_codes(post_request, 200)
                    request_id = post_request.json()['requestId']
                else:
                    printer('Creating request...')
                    account = choice(accounts_fixture.accounts)
                    accounts_fixture.create_request(account['accountId'])
                    request_id = accounts_fixture.request_id
        else:
            printer('Request already created')
            request_id = accounts_fixture.request_id

        printer('GET request')
        response = accounts_fixture.api.ext_api.get_request(request_id)
        asserts_codes(response, 200)

        if accounts_fixture.request_id is not None:
            for prep, user_id in [('By', accounts_fixture.primary_user_id), ('From', accounts_fixture.secondary_user_id)]:
                assert response.json()[f'requested{prep}User']['userId'] == user_id and print_success(f'requested{prep}User - userId is correct')

        validate_schema('request.json', response)
        values_exist(response.json(), 'responseNote')

    @pytest.mark.parent
    def test_approve_request(self, accounts_fixture, storage):
        if accounts_fixture.api.env_data.primary_role == 0:
            pytest.skip('not applicable for child for the demo')
        accounts_fixture.get_dashboard()

        request_id = accounts_fixture.request_id
        if request_id is None:
            print_pink('Logging in as the child to create request...')
            child_dash = accounts_fixture.api.secondary.get_dashboard()
            asserts_codes(child_dash, 200)

            account = choice(child_dash.json()['dashboard']['accounts'])
            body = post_request_body(accounts_fixture.primary_user_id, account['accountId'])

            print_pink('Creating request as the secondary user...')
            post_request = accounts_fixture.api.secondary.post_requests(body)
            asserts_codes(post_request, 200)
            request_id = post_request.json()['requestId']
            min_balance = body['amount']
        else:
            min_balance = getattr(storage, 'request')['amount']

        printer('GET possible source accounts list')
        source_response = accounts_fixture.api.ext_api.get_transfers_source()
        asserts_codes(source_response, 200)

        suitable_accounts = list(filter(lambda x: x['availableBalance'] >= min_balance, source_response.json()))
        account_id = choice(suitable_accounts)['accountId']

        body = {
            "transferAccountId": account_id,
            "note": get_random_string()
        }

        printer('POST approve request')
        response = accounts_fixture.api.ext_api.post_approve_requests(request_id, body)
        asserts_codes(response, 200)

        accounts_fixture.request_id = None
        accounts_fixture.approved_request_id = request_id
        storage.approved_request = response.json()

        assert response.json()['status'] == 'approved' and print_success('status: approved')
        validate_schema('request.json', response)
        values_exist(response.json())

    @pytest.mark.parent
    def test_deny_request(self, accounts_fixture, storage):
        if accounts_fixture.api.env_data.primary_role == 0:
            pytest.skip('not applicable for child for the demo')
        accounts_fixture.get_dashboard()

        request_id = accounts_fixture.request_id
        if request_id is None:
            print_pink('Logging in as the child to create request...')
            child_dash = accounts_fixture.api.secondary.get_dashboard()
            asserts_codes(child_dash, 200)

            account = choice(child_dash.json()['dashboard']['accounts'])
            body = post_request_body(accounts_fixture.primary_user_id, account['accountId'])

            printer('Creating request as the secondary user...')
            post_request = accounts_fixture.api.secondary.post_requests(body)
            asserts_codes(post_request, 200)
            request_id = post_request.json()['requestId']

        # request_id = '22bb8654-146c-495b-8a1a-42c4ba5ca6e1'

        printer('POST deny request')
        response = accounts_fixture.api.ext_api.post_deny_requests(request_id)
        asserts_codes(response, 200)

        accounts_fixture.request_id = None
        accounts_fixture.denied_request_id = request_id

        assert response.json()['status'] == 'denied' and print_success('status: denied')
        validate_schema('request.json', response)
        values_exist(response.json(), 'responseNote')

    @pytest.mark.parametrize('approved', [True, False], ids=['approved', 'denied'])  # approved/denied by a parent
    def test_processed_request_removed_from_dashboard(self, accounts_fixture, storage, approved):
        primary_role = accounts_fixture.api.env_data.primary_role

        request_id = [accounts_fixture.denied_request_id, accounts_fixture.approved_request_id][approved]
        if request_id is None:
            printer(f"Let's create {('denied', 'approved')[approved]} request")
            if primary_role == 1:
                [self.test_deny_request, self.test_approve_request][approved](accounts_fixture, storage)
            else:  # it's not possible to deny/approve request from the child's side
                if accounts_fixture.request_id is None:
                    printer('Creating a request...')
                    account = choice(accounts_fixture.accounts)
                    accounts_fixture.create_request(account['accountId'])
                print_pink('Logging in as a parent')
                if approved:
                    printer('GET possible source accounts list')
                    source_response = accounts_fixture.api.secondary.get_transfers_source()
                    asserts_codes(source_response, 200)
                    account_id = choice(source_response.json())['accountId']

                    body = {
                        "transferAccountId": account_id,
                        "note": get_random_string()
                    }

                    printer('POST approve request')
                    response = accounts_fixture.api.secondary.post_approve_requests(accounts_fixture.request_id, body)
                    asserts_codes(response, 200)

                    accounts_fixture.approved_request_id, accounts_fixture.request_id = accounts_fixture.request_id, None
                    storage.approved_request = response.json()
                else:
                    printer('POST deny request')
                    response = accounts_fixture.api.secondary.post_deny_requests(accounts_fixture.request_id)
                    asserts_codes(response, 200)

                    accounts_fixture.denied_request_id, accounts_fixture.request_id = accounts_fixture.request_id, None
            request_id = [accounts_fixture.denied_request_id, accounts_fixture.approved_request_id][approved]

        printer(f'Searching for {request_id=} in {("child", "parent")[primary_role]} dashboard')
        dashboard = accounts_fixture.get_dashboard(force=True)
        asserts_codes(dashboard, 200)

        if primary_role == 1:
            requests_list = chain.from_iterable((x['sentRequests'] for x in dashboard.json()['dashboard']['children']))
        else:
            requests_list = dashboard.json()['dashboard']['sentRequests']
        requests_ids = list(map(lambda x: x['requestId'], requests_list))

        assert request_id not in requests_ids and print_success('request removed from the dashboard')

    def test_approved_transaction_appears_in_transaction_history(self, accounts_fixture, storage):
        accounts_fixture.get_dashboard()
        approved_request = getattr(storage, 'approved_request', None)
        if approved_request is None:
            printer('Approved request does not exist yet..')
            if accounts_fixture.api.env_data.primary_role == 1:
                self.test_approve_request(accounts_fixture, storage)
            else:
                if accounts_fixture.request_id is None:
                    printer('Creating a request...')
                    account = choice(accounts_fixture.accounts)
                    accounts_fixture.create_request(account['accountId'])
                print_pink('Logging in as a parent')
                printer('GET possible source accounts list')
                source_response = accounts_fixture.api.secondary.get_transfers_source()
                asserts_codes(source_response, 200)
                account_id = choice(source_response.json())['accountId']

                body = {
                    "transferAccountId": account_id,
                    "note": get_random_string()
                }

                printer('POST approve request')
                response = accounts_fixture.api.secondary.post_approve_requests(accounts_fixture.request_id, body)
                asserts_codes(response, 200)

                accounts_fixture.approved_request_id, accounts_fixture.request_id = accounts_fixture.request_id, None
                storage.approved_request = response.json()
            approved_request = getattr(storage, 'approved_request')

        account_id = approved_request['depositAccount']['accountId']
        printer('GET transactions', f'account_id: {account_id}')
        response = accounts_fixture.api.ext_api.get_transactions(account_id)

        def filter_transactions(tr: dict) -> bool:
            transfer_user = tr.get('transferUser', None)
            if transfer_user is None:
                return False
            for key, value in [('amount', approved_request['amount']), ('description', approved_request['requestNote'])]:
                if tr[key] != value:
                    return False
            for key, value in [('userId', approved_request['requestedFromUser']['userId']),
                               ('nickname', approved_request['requestedFromUser']['nickname'])]:
                if transfer_user[key] != value:
                    return False
            return True

        filtered_transactions = list(filter(filter_transactions, response.json()['items']))
        assert len(filtered_transactions) == 1 and print_success('transactions found!')
        pprint(filtered_transactions[0])


class TestRequestNegative:

    @pytest.mark.parent
    def test_parent_cannot_approve_request_with_child_account_id(self, accounts_fixture):
        if accounts_fixture.api.env_data.primary_role == 0:
            pytest.skip('not applicable for child for the demo')
        accounts_fixture.get_dashboard()

        request_id = accounts_fixture.request_id
        if request_id is None:
            print_pink('Logging in as the child to create request...')
            child_dash = accounts_fixture.api.secondary.get_dashboard()
            asserts_codes(child_dash, 200)

            account = choice(child_dash.json()['dashboard']['accounts'])
            body = post_request_body(accounts_fixture.primary_user_id, account['accountId'])

            print_pink('Creating request as the secondary user...')
            post_request = accounts_fixture.api.secondary.post_requests(body)
            asserts_codes(post_request, 200)
            request_id = post_request.json()['requestId']

        dashboard = accounts_fixture.get_dashboard(force=True)
        for child in dashboard.json()['dashboard']['children']:
            if request_id in [r['requestId'] for r in child['sentRequests']]:
                account_id = choice(child['accounts'])['accountId']

        body = {
            "transferAccountId": account_id,
            "note": get_random_string()
        }

        printer('POST approve request')
        response = accounts_fixture.api.ext_api.post_approve_requests(request_id, body)
        asserts_codes(response, 400)