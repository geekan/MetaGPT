# 添加代码语法高亮显示
from pygments import highlight as highlight_
from pygments.formatters import HtmlFormatter, TerminalFormatter
from pygments.lexers import PythonLexer, SqlLexer


def highlight(code: str, language: str = "python", formatter: str = "terminal"):
    """Syntax highlights the given code.

    This function uses Pygments to highlight code in either Python or SQL syntax
    and outputs it using either terminal or HTML formatting.

    Args:
        code: The source code to be highlighted.
        language: The programming language of the code ('python' or 'sql').
        formatter: The output format ('terminal' or 'html').

    Returns:
        The syntax-highlighted code as a string.

    Raises:
        ValueError: If an unsupported language or formatter is specified.
    """
    # 指定要高亮的语言
    if language.lower() == "python":
        lexer = PythonLexer()
    elif language.lower() == "sql":
        lexer = SqlLexer()
    else:
        raise ValueError(f"Unsupported language: {language}")

    # 指定输出格式
    if formatter.lower() == "terminal":
        formatter = TerminalFormatter()
    elif formatter.lower() == "html":
        formatter = HtmlFormatter()
    else:
        raise ValueError(f"Unsupported formatter: {formatter}")

    # 使用 Pygments 高亮代码片段
    return highlight_(code, lexer, formatter)
