from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM


class Define:
    def __init__(self):
        self.nodes = []
        self.vars = {}

    def add_node(self, node):
        self.nodes.append(node)

    async def run(self, context):
        # 构建动态的 ActionNode 图
        action_nodes = []
        for node in self.nodes:
            if isinstance(node, ActionNode):
                node = CallActionNode(node, self, None)  # consider input data None
            # 可以根据需要设置动态的连接关系、属性等等
            action_nodes.append(node)

        # 执行计算
        for node in action_nodes:
            await node.compute(context)

        # 返回结果
        return context


# represents ActionNodeClass
class ActionNodeClassNode:
    def __init__(self, model, context_symbol):
        self.model = model  # the pydantic model which ActionNode.from_pydantic(model)
        self.context_symbol = context_symbol

    async def compute(self, context):
        # 根据节点定义执行具体的计算
        action_node = ActionNode.from_pydantic(self.model)

        return await CallActionNode(action_node, self.context_symbol, modifier_symbol=SymbolTemplate(" {i}")).compute(
            context
        )


class CallActionNode:
    def __init__(self, node, context_symbol, modifier_symbol=None):
        self.node = node
        self.context_symbol = context_symbol
        self.modifier_symbol = modifier_symbol

    async def compute(self, context):
        # 根据节点定义执行具体的计算
        v = await self.context_symbol.compute(context)
        await self.node.fill(context=v, llm=LLM())
        key = self.node.key
        if self.modifier_symbol:
            key = key + await self.modifier_symbol.compute(context)
        context.set_symbol(key, self.node)
        return self.node


# 定义一些具体的计算节点
class AddNode:
    def compute(self, input_data):
        return input_data + 2


class MultiplyNode:
    def compute(self, input_data):
        return input_data * 3


class ControlFlowNode:
    def __init__(self, condition, node):
        self.condition = condition
        self.action_node = node

    def compute(self, input_data):
        if self.condition:
            return self.action_node.compute()


# 定义条件判断节点
class ConditionNode:
    def __init__(self, input_data):
        self.input_data = input_data

    async def compute(self, context):
        return bool(self.input_data)


class ConstantNode:
    def __init__(self, input_data):
        self.input_data = input_data

    async def compute(self, context):
        return self.input_data


class IfNode:
    def __init__(self, condition, action_node):
        self.condition = condition
        self.action_node = action_node

    async def compute(self, context):
        if self.condition.evaluate(context):
            self.action_node.execute(context)


class LoopNode:
    def __init__(self, range_start, range_end, action_node, loop_var):
        self.range_start = range_start
        self.range_end = range_end
        self.action_node = action_node
        self.loop_var = loop_var

    async def compute(self, context):
        result = []
        for i in range(self.range_start, self.range_end + 1):
            result.append(self.action_node.execute(context={self.loop_var: i}))
        return result


class ForeachNode:
    def __init__(self, items, provider_node, body_node, loop_var="i"):
        self.items = items
        self.provider_node = provider_node
        self.loop_var = loop_var
        self.body_node = body_node

    async def compute(self, context):
        result = []
        if isinstance(self.items, str):
            items = self.provider_node.instruct_content.dict()[self.items]
        else:
            items = self.items
        for item in items:
            context.set_symbol(self.loop_var, item)
            result.append(await self.body_node.compute(context=context))
        return result


class SequentialNode:
    def __init__(self, nodes):
        self.nodes = nodes

    def compute(self, context):
        result = []
        for node in self.nodes:
            result.append(node.execute(context=context))
        return result


# or SymbolSpace?
class SymbolTable:
    def __init__(self, symbols={}, parent=None):
        self.symbols = symbols
        self.parent = parent  # not implemented now

    def set_symbol(self, symbol_name, symbol_value):
        self.symbols[symbol_name] = symbol_value

    def get_symbol(self, symbol_name):
        return self.symbols.get(symbol_name)


class SymbolSet:
    def __init__(self, symbol_name):
        self.symbol_name = symbol_name

    async def compute(self, context, symbol_table):
        symbol_value = context[self.symbol_name]
        symbol_table.set_symbol(self.symbol_name, symbol_value)


class SymbolGet:
    def __init__(self, symbol_name, output_key):
        self.symbol_name = symbol_name
        self.output_key = output_key

    async def compute(self, context, symbol_table):
        symbol_value = symbol_table.get_symbol(self.symbol_name)
        context[self.output_key] = symbol_value


class SymbolTemplate:
    def __init__(self, template):
        self.template = template

    async def compute(self, context):
        return self.template.format(**context.symbols)
