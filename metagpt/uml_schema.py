#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/8 22:12
@Author  : alexanderwu
@File    : schema.py
@Modified By: mashenquan, 2023-10-31. According to Chapter 2.2.1 of RFC 116:
        Replanned the distribution of responsibilities and functional positioning of `Message` class attributes.
@Modified By: mashenquan, 2023/11/22.
        1. Add `Document` and `Documents` for `FileRepository` in Section 2.2.3.4 of RFC 135.
        2. Encapsulate the common key-values set to pydantic structures to standardize and unify parameter passing
        between actions.
        3. Add `id` to `Message` according to Section 2.2.3.1.1 of RFC 135.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from metagpt.repo_parser import DotClassInfo


# mermaid class view
class UMLClassMeta(BaseModel):
    name: str = ""
    visibility: str = ""

    @staticmethod
    def name_to_visibility(name: str) -> str:
        if name == "__init__":
            return "+"
        if name.startswith("__"):
            return "-"
        elif name.startswith("_"):
            return "#"
        return "+"


class UMLClassAttribute(UMLClassMeta):
    value_type: str = ""
    default_value: str = ""

    def get_mermaid(self, align=1) -> str:
        content = "".join(["\t" for i in range(align)]) + self.visibility
        if self.value_type:
            content += self.value_type.replace(" ", "") + " "
        name = self.name.split(":", 1)[1] if ":" in self.name else self.name
        content += name
        if self.default_value:
            content += "="
            if self.value_type not in ["str", "string", "String"]:
                content += self.default_value
            else:
                content += '"' + self.default_value.replace('"', "") + '"'
        # if self.abstraction:
        #     content += "*"
        # if self.static:
        #     content += "$"
        return content


class UMLClassMethod(UMLClassMeta):
    args: List[UMLClassAttribute] = Field(default_factory=list)
    return_type: str = ""

    def get_mermaid(self, align=1) -> str:
        content = "".join(["\t" for i in range(align)]) + self.visibility
        name = self.name.split(":", 1)[1] if ":" in self.name else self.name
        content += name + "(" + ",".join([v.get_mermaid(align=0) for v in self.args]) + ")"
        if self.return_type:
            content += " " + self.return_type.replace(" ", "")
        # if self.abstraction:
        #     content += "*"
        # if self.static:
        #     content += "$"
        return content


class UMLClassView(UMLClassMeta):
    attributes: List[UMLClassAttribute] = Field(default_factory=list)
    methods: List[UMLClassMethod] = Field(default_factory=list)

    def get_mermaid(self, align=1) -> str:
        content = "".join(["\t" for i in range(align)]) + "class " + self.name + "{\n"
        for v in self.attributes:
            content += v.get_mermaid(align=align + 1) + "\n"
        for v in self.methods:
            content += v.get_mermaid(align=align + 1) + "\n"
        content += "".join(["\t" for i in range(align)]) + "}\n"
        return content

    @classmethod
    def load_dot_class_info(cls, dot_class_info: DotClassInfo) -> UMLClassView:
        visibility = UMLClassView.name_to_visibility(dot_class_info.name)
        class_view = cls(name=dot_class_info.name, visibility=visibility)
        for i in dot_class_info.attributes.values():
            visibility = UMLClassAttribute.name_to_visibility(i.name)
            attr = UMLClassAttribute(name=i.name, visibility=visibility, value_type=i.type_, default_value=i.default_)
            class_view.attributes.append(attr)
        for i in dot_class_info.methods.values():
            visibility = UMLClassMethod.name_to_visibility(i.name)
            method = UMLClassMethod(name=i.name, visibility=visibility, return_type=i.return_args.type_)
            for j in i.args:
                arg = UMLClassAttribute(name=j.name, value_type=j.type_, default_value=j.default_)
                method.args.append(arg)
            method.return_type = i.return_args.type_
            class_view.methods.append(method)
        return class_view
