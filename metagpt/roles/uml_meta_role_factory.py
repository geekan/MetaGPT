#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/7
@Author  : mashenquan
@File    : uml_meta_role_factory.py
@Desc   : I am attempting to incorporate certain symbol concepts from UML into MetaGPT, enabling it to have the
            ability to freely construct flows through symbol concatenation. Simultaneously, I am also striving to
            make these symbols configurable and standardized, making the process of building flows more convenient.
            For more about `fork` node in activity diagrams, see: `https://www.uml-diagrams.org/activity-diagrams.html`
"""

from metagpt.roles.fork_meta_role import ForkMetaRole
from metagpt.roles.uml_meta_role_options import UMLMetaRoleOptions


class UMLMetaRoleFactory:
    """Factory of UML activity role classes"""

    @classmethod
    def create_roles(cls, role_configs, **kwargs):
        """Generate the flow of the project based on the configuration in the format of config/pattern/template.yaml.

        :param role_configs: `roles` field of template.yaml
        :param kwargs: Parameters passed in format: `python your_script.py --param1=value1 --param2=value2`

        """
        roles = []
        for m in role_configs:
            opt = UMLMetaRoleOptions(**m)
            constructor = cls.CONSTRUCTORS.get(opt.role_type)
            if constructor is None:
                raise NotImplementedError(
                    f"{opt.role_type} is not implemented"
                )
            r = constructor(role_options=m, **kwargs)
            roles.append(r)
        return roles

    CONSTRUCTORS = {
        "fork": ForkMetaRole,
        # TODO: add more activity node constructor here..
    }
