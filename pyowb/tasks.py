import sys
import xml.sax.saxutils
from .keywords import *

def xml_escape(string):
    return xml.sax.saxutils.quoteattr(string)

_global_auto_id = 100
def _next_global_auto_id():
    global _global_auto_id
    auto_id = '_auto' + str(_global_auto_id)
    _global_auto_id += 1
    return auto_id

def parse_category(name):
    index_of_dash = name.find('-')
    if index_of_dash == -1:
        return ''
    return name[0:index_of_dash].rstrip()

def has_children(task):
    return (CHILDREN in task) and (len(task[CHILDREN]) != 0)


def sanitize_tasks(plan, id_to_task, add_child_dependencies):
    def _sanitize_recursive(task, auto_predecessor_stack):
        if ID not in task:
            task[ID] = _next_global_auto_id()
        id_to_task[task[ID]] = task

        if DEPS not in task:
            task[DEPS] = []
        if add_child_dependencies:
            for auto_predecessor_id in auto_predecessor_stack:
                if auto_predecessor_id:
                    task[DEPS].append(auto_predecessor_id)
        elif len(auto_predecessor_stack):
            auto_predecessor_id = auto_predecessor_stack[-1]
            if auto_predecessor_id:
                task[DEPS].append(auto_predecessor_id)

        children = task.get(CHILDREN, None)
        if children:
            auto_predecessor_stack.append(None)
            in_sequence = False
            for child in children:
                if child == SEQUENCE:
                    auto_predecessor_stack[-1] = None
                    in_sequence = True
                elif child == PARALLEL:
                    auto_predecessor_stack[-1] = None
                    in_sequence = False
                else:
                    _sanitize_recursive(child, auto_predecessor_stack)
                    if add_child_dependencies:
                        task[DEPS].append(child[ID])
                    if in_sequence:
                        auto_predecessor_stack[-1] = child[ID]
            auto_predecessor_stack.pop()

    auto_predecessor_stack = []
    _sanitize_recursive(plan, auto_predecessor_stack)
