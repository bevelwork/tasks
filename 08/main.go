package main

import (
	"context"
	"flag"
	"fmt"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	elb "github.com/aws/aws-sdk-go-v2/service/elasticloadbalancingv2"
	"github.com/aws/aws-sdk-go-v2/service/elasticloadbalancingv2/types"
	"log"
	"strconv"
)

const (
	ENABLE                  = "enable"
	DISABLE                 = "disable"
	ENABLED_PRIORITY_LEVEL  = 95
	DISABLED_PRIORITY_LEVEL = 500
)

func contains(list []string, str string) bool {
	for _, v := range list {
		if v == str {
			return true
		}
	}
	return false
}

func main() {
	action := flag.String(
		"action",
		"",
		"Action to perform. Options: enable, disable",
	)
	flag.Parse()
	log.Printf("action: %v", *action)
	if *action == "" {
		log.Fatalf("action is required")
	} else if *action != "enable" && *action != "disable" {
		log.Fatalf("action must be either enable or disable")
	}

	listOfLB := []string{
		"admin-gui",
		"mono",
		"admin",
	}
	cfg, err := config.LoadDefaultConfig(context.TODO(),
		config.WithRegion("us-east-1"),
	)
	if err != nil {
		log.Fatalf("unable to load SDK config, %v", err)
	}
	client := elb.NewFromConfig(cfg)
	params := &elb.DescribeLoadBalancersInput{
		LoadBalancerArns: []string{},
	}
	resp, err := client.DescribeLoadBalancers(context.Background(), params)
	if err != nil {
		log.Fatalf("failed to describe load balancers, %v", err)
	}
	lbArnsToInteractWith := []string{}
	for _, lb := range resp.LoadBalancers {
		log.Printf(
			"LoadBalancer: %v :: %v",
			aws.ToString(lb.LoadBalancerName),
			aws.ToString(lb.LoadBalancerArn),
		)
		if contains(listOfLB, aws.ToString(lb.LoadBalancerName)) {
			lbArnsToInteractWith = append(lbArnsToInteractWith, aws.ToString(lb.LoadBalancerArn))
		}
	}
	for _, lbArn := range lbArnsToInteractWith {
		listeners, err := client.DescribeListeners(context.Background(), &elb.DescribeListenersInput{
			LoadBalancerArn: &lbArn,
		})
		if err != nil {
			log.Fatalf("failed to describe listeners, %v", err)
		}
		rulesToModify := []types.Rule{}
		for _, listener := range listeners.Listeners {
			if *listener.Port == 443 {
				rules, err := client.DescribeRules(context.Background(), &elb.DescribeRulesInput{
					ListenerArn: listener.ListenerArn,
				})
				if err != nil {
					log.Fatalf("failed to describe rules, %v", err)
				}
				for _, rule := range rules.Rules {
					tags, err := client.DescribeTags(context.Background(), &elb.DescribeTagsInput{
						ResourceArns: []string{*rule.RuleArn},
					})
					if err != nil {
						log.Fatalf("failed to describe tags, %v", err)
					}
					for _, tag := range tags.TagDescriptions {
						for _, tagValue := range tag.Tags {
							if *tagValue.Key == "Name" && *tagValue.Value == "maintenance" {
								log.Printf(
									"Rule: %v :: %v :: %v",
									*tagValue.Value,
									*rule.Priority,
									*rule.RuleArn,
								)
								if *action == ENABLE && *rule.Priority != strconv.Itoa(ENABLED_PRIORITY_LEVEL) {
									fmt.Println("Enabling maintenance mode for rule: ", *rule.RuleArn)
									rulesToModify = append(rulesToModify, rule)
								} else if *action == DISABLE && *rule.Priority != strconv.Itoa(DISABLED_PRIORITY_LEVEL) {
									fmt.Println("Disabling maintenance mode for rule: ", *rule.RuleArn)
									rulesToModify = append(rulesToModify, rule)
								} else {
									fmt.Println("Maintenance mode already correct for rule: ", *rule.RuleArn, *rule.Priority)
								}
							}
						}
					}
				}
			}
		}
		for _, rule := range rulesToModify {
			if *action == ENABLE {
				fmt.Println("Enabling maintenance mode for rule: ", *rule.RuleArn)
				_, err := client.SetRulePriorities(context.Background(), &elb.SetRulePrioritiesInput{
					RulePriorities: []types.RulePriorityPair{
						{
							Priority: aws.Int32(ENABLED_PRIORITY_LEVEL),
							RuleArn:  rule.RuleArn,
						},
					},
				})
				if err != nil {
					log.Fatalf("failed to set rule priorities, %v", err)
				}
			} else if *action == DISABLE {
				_, err := client.SetRulePriorities(context.Background(), &elb.SetRulePrioritiesInput{
					RulePriorities: []types.RulePriorityPair{
						{
							Priority: aws.Int32(DISABLED_PRIORITY_LEVEL),
							RuleArn:  rule.RuleArn,
						},
					},
				})
				if err != nil {
					log.Fatalf("failed to set rule priorities, %v", err)
				}
			}
		}
	}
}
