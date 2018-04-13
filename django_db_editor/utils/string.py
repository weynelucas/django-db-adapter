import re


def replace_prefix(text, prefix, repl):
    return re.sub(
        r'^{prefix}'.format(prefix=prefix), 
        repl, text, flags=re.I
    )


def replace_suffix(text, suffix, repl):
    return re.sub(
        r'{suffix}$'.format(suffix=suffix), 
        repl, text, flags=re.I
    )