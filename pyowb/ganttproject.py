# Python plan -> Open Workbench XML converter.
#
#   Python plan defines a Work Breakdown Structure where
#   tasks are dictionaries and children are defined in a list.
#   Children can contain sequences, to simplify data input;
#   sequenced tasks are automatically chained (dependencies).

import sys
import math
from datetime import datetime, timedelta
from .keywords import *
from .tasks import *

# NOTE: arbitrarily chosen start date
_global_start_date = datetime(year=2016, month=10, day=10)


def _date_as_gp_string(date):
    return date.strftime('%Y-%m-%d')

def _insert_dependency(deps, successor, predecessor):
    if predecessor not in deps:
        deps[predecessor] = {}
    deps[predecessor][successor] = True

def _validate_tasks(id_to_task, deps):
    for task in id_to_task.values():
        for predecessor_id in task[DEPS]:
            if predecessor_id not in id_to_task:
                sys.stderr.write('WARNING: ID={task[ID]} NAME={task[NAME]} : unknown dependency "{predecessor_id}"\n'.format(**locals()))
            _insert_dependency(deps, task[ID], predecessor_id)

# Returns id_to_intid: dict(task_id, int_id)
def _generate_integer_ids(id_to_task):
    intid = 0
    id_to_intid = {}
    for task_id in sorted(id_to_task.keys()):
        id_to_intid[task_id] = intid
        intid += 1
    return id_to_intid

    
def _output_tasks_recursive(outfile, id_to_intid, deps, task, level):
    _effort_in_days = task.get(EFFORT, 0)
    _duration = 1 if has_children(task) else _effort_in_days

    _indent = '    '*level
    _category = parse_category(task[NAME])
    _name = xml_escape_attr(task[NAME])
    _intid = id_to_intid[task[ID]]
    _desc = task.get(DESC, None)
    _start_date = _date_as_gp_string(_global_start_date)
    _expand = 'true'

    successor_ids = deps.get(task[ID], None)
        
    task_tag = '        {_indent}<task id="{_intid}" name={_name} color="#8cb6ce" meeting="false" start="{_start_date}" duration="{_duration}" complete="0" expand="{_expand}">\n'.format(**locals())
    outfile.write(task_tag)
    if _desc:
        outfile.write('            {_indent}<notes><![CDATA[{_desc}]]></notes>\n'.format(**locals()))
    if successor_ids:
        for successor_id in successor_ids.keys():
            successor_intid = id_to_intid[successor_id]
            outfile.write('            {_indent}<depend id="{successor_intid}" type="2" difference="0" hardness="Strong"/>\n'.format(**locals()))

    children = task.get(CHILDREN, None)
    if children:
        for child in children:
            if isinstance(child, str):
                continue
            else:
                _output_tasks_recursive(outfile, id_to_intid, deps, child, level+1)

    outfile.write('        {_indent}</task>\n'.format(**locals()))

def _output_tasks(outfile, id_to_intid, deps, plan):
    prefix = '''
    <tasks empty-milestones="true">
        <taskproperties>
            <taskproperty id="tpd0" name="type" type="default" valuetype="icon"/>
            <taskproperty id="tpd1" name="priority" type="default" valuetype="icon"/>
            <taskproperty id="tpd2" name="info" type="default" valuetype="icon"/>
            <taskproperty id="tpd3" name="name" type="default" valuetype="text"/>
            <taskproperty id="tpd4" name="begindate" type="default" valuetype="date"/>
            <taskproperty id="tpd5" name="enddate" type="default" valuetype="date"/>
            <taskproperty id="tpd6" name="duration" type="default" valuetype="int"/>
            <taskproperty id="tpd7" name="completion" type="default" valuetype="int"/>
            <taskproperty id="tpd8" name="coordinator" type="default" valuetype="text"/>
            <taskproperty id="tpd9" name="predecessorsr" type="default" valuetype="text"/>
        </taskproperties>
'''
    suffix = '''
    </tasks>
'''

    outfile.write(prefix.lstrip('\n'))
    _output_tasks_recursive(outfile, id_to_intid, deps, plan, 0)
    outfile.write(suffix.lstrip('\n'))
    
    
def _output_main_file(outfile, plan):
    prefix = '''
<?xml version="1.0" encoding="UTF-8"?>
<project name="Untitled" company="" webLink="http://" view-date="2017-01-15" view-index="0" gantt-divider-location="353" resource-divider-location="300" version="2.8.1" locale="en_US">
    <description/>
    <view zooming-state="default:4" id="gantt-chart">
        <field id="tpd3" name="Name" width="199" order="0"/>
        <field id="tpd4" name="Begin date" width="75" order="1"/>
        <field id="tpd5" name="End date" width="75" order="2"/>
    </view>
    <view id="resource-table">
        <field id="0" name="Name" width="210" order="0"/>
        <field id="1" name="Default role" width="86" order="1"/>
    </view>
    <!-- -->
    <calendars>
        <day-types>
            <day-type id="0"/>
            <day-type id="1"/>
            <default-week id="1" name="default" sun="1" mon="0" tue="0" wed="0" thu="0" fri="0" sat="1"/>
            <only-show-weekends value="false"/>
            <overriden-day-types/>
            <days/>
        </day-types>
    </calendars>
'''
    suffix = '''
    <resources>
    </resources>
    <allocations>
    </allocations>
    <vacations/>
    <previous/>
    <roles roleset-name="Default"/>
    <roles roleset-name="SoftwareDevelopment"/>
</project>
</WORKBENCH_PROJECT>'''

    # key = ID string, value = task dict
    id_to_task = {}
    sanitize_tasks(plan, id_to_task, add_child_dependencies=False)
    # key = predecessor, value = {sucessor:True}
    deps = {}
    _validate_tasks(id_to_task, deps)
    # key = task_id, value = intid
    id_to_intid = _generate_integer_ids(id_to_task)

    outfile.write(prefix.lstrip('\n'))
    _output_tasks(outfile, id_to_intid, deps, plan)
    outfile.write(suffix.lstrip('\n'))


def plan_to_ganttproject(filename, plan):
    with open(filename, 'wt') as outfile:
        _output_main_file(outfile, plan)
