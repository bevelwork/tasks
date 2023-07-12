#--- Ingress for Mobile Envoy Gateway ECS Task
resource "aws_vpc_security_group_ingress_rule" "mobile_envoy_gateway_ecs_task_ingress" {
  for_each                     = toset([local.service.mobile_envoy_gateway.listen_port, "9901"])
  security_group_id            = module.mobile_envoy_gateway.security_group_id
  from_port                    = each.value
  to_port                      = each.value
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.mobile_alb.id
  description                  = "Ingress from Mobile ALB to Mobile Envoy Gateway ECS Service"
}
#--- Egress for Mobile Envoy Gateway ECS Task
resource "aws_vpc_security_group_egress_rule" "mobile_envoy_gateway_ecs_task_egress" {
  security_group_id            = module.mobile_envoy_gateway.security_group_id
  from_port                    = local.service.stratus_mobilegateway_apfcu.listen_port
  to_port                      = local.service.stratus_mobilegateway_apfcu.listen_port
  ip_protocol                  = "tcp"
  referenced_security_group_id = module.stratus_mobilegateway.security_group_id
  description                  = "Egress from Mobile Envoy Gateway to MobileGateway ECS"
}
#--- Ingress for MobileGateway ECS Task
resource "aws_vpc_security_group_ingress_rule" "mobilegateway_ecs_task_ingress" {
  for_each                     = toset([local.service.stratus_mobilegateway_apfcu.listen_port, "9901"])
  security_group_id            = module.stratus_mobilegateway.security_group_id
  from_port                    = each.value
  to_port                      = each.value
  ip_protocol                  = "tcp"
  referenced_security_group_id = module.mobile_envoy_gateway.security_group_id
  description                  = "Ingress from MobileGateway ALB to Gateway ECS Service"
}


#--- Ingress for Admin Envoy Gateway ECS Task
resource "aws_vpc_security_group_ingress_rule" "admin_envoy_gateway_ecs_task_ingress" {
  for_each                     = toset([local.service.admin_envoy_gateway.listen_port, "9901"])
  security_group_id            = module.admin_envoy_gateway.security_group_id
  from_port                    = each.value
  to_port                      = each.value
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.admin_alb.id
  description                  = "Ingress from Admin ALB to Admin Envoy Gateway ECS Service"
}
#--- Egress for Admin Envoy Gateway ECS Task
resource "aws_vpc_security_group_egress_rule" "admin_envoy_gateway_ecs_task_egress" {
  security_group_id            = module.admin_envoy_gateway.security_group_id
  from_port                    = local.service.stratus_admingateway_apfcu.listen_port
  to_port                      = local.service.stratus_admingateway_apfcu.listen_port
  ip_protocol                  = "tcp"
  referenced_security_group_id = module.stratus_admingateway.security_group_id
  description                  = "Egress from Admin Envoy Gateway to AdminGateway ECS"
}

#--- Ingress for AdminGateway ECS Task
resource "aws_vpc_security_group_ingress_rule" "admingateway_ecs_task_ingress" {
  for_each                     = toset([local.service.stratus_admingateway_apfcu.listen_port, "9901"])
  security_group_id            = module.stratus_admingateway.security_group_id
  from_port                    = each.value
  to_port                      = each.value
  ip_protocol                  = "tcp"
  referenced_security_group_id = module.admin_envoy_gateway.security_group_id
  description                  = "Ingress from Admin Envoy Gateway to Gateway ECS Service"
}

#--- Ingress for Nucleus ECS Task
resource "aws_vpc_security_group_ingress_rule" "nucleus_ecs_task_ingress_mobile" {
  for_each                     = toset([local.service.stratus_nucleus_apfcu.listen_port, "9901"])
  security_group_id            = module.stratus_nucleus_apfcu.security_group_id
  from_port                    = each.value
  to_port                      = each.value
  ip_protocol                  = "tcp"
  referenced_security_group_id = module.stratus_mobilegateway.security_group_id
  description                  = "Ingress to Nucleus ECS Service"
}
resource "aws_vpc_security_group_ingress_rule" "nucleus_ecs_task_ingress_admin" {
  for_each                     = toset([local.service.stratus_nucleus_apfcu.listen_port, "9901"])
  security_group_id            = module.stratus_nucleus_apfcu.security_group_id
  from_port                    = each.value
  to_port                      = each.value
  ip_protocol                  = "tcp"
  referenced_security_group_id = module.stratus_admingateway.security_group_id
  description                  = "Ingress to Nucleus ECS Service"
}
#--- Ingress for Adapter ECS Task
resource "aws_vpc_security_group_ingress_rule" "adapter_ecs_task_ingress" {
  for_each                     = toset([local.service.stratus_adapter_apfcu.listen_port, "9901"])
  security_group_id            = module.stratus_adapter_apfcu.security_group_id
  from_port                    = each.value
  to_port                      = each.value
  ip_protocol                  = "tcp"
  referenced_security_group_id = module.stratus_nucleus_apfcu.security_group_id
  description                  = "Ingress from Backend ECS Task to Adapter ECS Service"
}

#--- Ingress for Stratus.Uno ECS Task
resource "aws_vpc_security_group_ingress_rule" "uno_ecs_task_ingress" {
  for_each                     = toset([local.service.stratus_uno.listen_port, "9901"])
  security_group_id            = module.stratus_uno.security_group_id
  from_port                    = each.value
  to_port                      = each.value
  ip_protocol                  = "tcp"
  referenced_security_group_id = module.stratus_adapter_apfcu.security_group_id
  description                  = "Ingress from Adapter ECS Task"
}

#--- Egress for Stratus.Uno ECS Task
resource "aws_vpc_security_group_egress_rule" "uno_ecs_task_egress" {
  security_group_id            = module.stratus_uno.security_group_id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.uno_rds.id
  description                  = "Egress TO RDS Instance"
}

resource "aws_vpc_security_group_egress_rule" "mobile_envoy_gateway_egress" {
  for_each = toset([
    # module.admin_gui.security_group_id, #TODO this should be added once readded to envoy
    module.stratus_adapter_apfcu.security_group_id,
    module.stratus_admingateway.security_group_id,
    module.stratus_nucleus_apfcu.security_group_id,
    module.stratus_uno.security_group_id,
    module.stratus_mobilegateway.security_group_id
  ])
  security_group_id            = module.mobile_envoy_gateway.security_group_id
  from_port                    = 9901
  to_port                      = 9901
  ip_protocol                  = "tcp"
  referenced_security_group_id = each.value
  description                  = "Egress from Mobile Envoy Gateway to all ECS Services"
}
resource "aws_vpc_security_group_egress_rule" "admin_envoy_gateway_egress" {
  for_each = toset([
    # module.admin_gui.security_group_id, #TODO this should be added once readded to envoy
    module.stratus_adapter_apfcu.security_group_id,
    module.stratus_admingateway.security_group_id,
    module.stratus_nucleus_apfcu.security_group_id,
    module.stratus_uno.security_group_id,
    module.stratus_mobilegateway.security_group_id
  ])
  security_group_id            = module.admin_envoy_gateway.security_group_id
  from_port                    = 9901
  to_port                      = 9901
  ip_protocol                  = "tcp"
  referenced_security_group_id = each.value
  description                  = "Egress from Admin Envoy Gateway to all ECS Services"
}