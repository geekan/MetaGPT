# -*- coding: utf-8 -*-
# @Desc    :


# def test_customer_service_serdeser():
#     role = CustomerService()
#     ser_role_dict = role.model_dump(exclude_none=True, mode="json")
#     assert "name" in ser_role_dict
#     assert "store" not in ser_role_dict
#
#     new_role = CustomerService(**ser_role_dict)
#     assert new_role.name == "Xiaomei"
#     assert new_role.profile == "Human customer service"


# def test_sales_serdeser():
#     role = Sales()
#     ser_role_dict = role.model_dump(exclude_none=True)
#     assert "name" in ser_role_dict
#     assert "store" not in ser_role_dict
#
#     new_role = Sales(**ser_role_dict)
#     assert new_role.name == "John Smith"
#     assert new_role.profile == "Retail Sales Guide"
