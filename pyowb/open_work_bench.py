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

# Start date is a monday.  End-date calculation needs to add 2 days per 5 (for weekends);
# starting on a monday simplifies calculation of the extra.
_global_start_date = datetime(year=2016, month=10, day=10)

def _insert_dependency(deps, successor, predecessor):
    if successor not in deps:
        deps[successor] = {}
    deps[successor][predecessor] = True

def _validate_tasks(id_to_task, deps):
    for task in id_to_task.values():
        for predecessor_id in task[DEPS]:
            if predecessor_id not in id_to_task:
                sys.stderr.write('WARNING: ID={task[ID]} NAME={task[NAME]} : unknown dependency "{predecessor_id}"\n'.format(**locals()))
            _insert_dependency(deps, task[ID], predecessor_id)

def _date_as_owb_string(date):
    return date.strftime('%Y-%m-%dT%H:%M:%S')


def _output_tasks_recursive(outfile, task, level):
    _effort_in_days = task.get(EFFORT, 0)
    _effort_in_calendar_days = _effort_in_days + math.floor((_effort_in_days - 1) / 5) * 2

    _category = parse_category(task[NAME])
    _name = xml_escape_attr(task[NAME])
    _id = xml_escape_attr(task[ID])
    _desc = xml_escape_attr(task.get(DESC, ' '))
    _level = level
    _summary = 'true' if has_children(task) else 'false'
    _start_date = _date_as_owb_string(_global_start_date)
    _end_date = _date_as_owb_string(_global_start_date + timedelta(days=_effort_in_calendar_days))

    task_xml = '''
        <Task
          category="{_category}" start="{_start_date}" finish="{_end_date}"
          proxy="false"
          critical="false" status="0" outlineLevel="{_level}" summary="{_summary}"
          milestone="false" name={_name} taskID={_id} fixed="false"
          locked="false" key="false" percComp="0.0" totalSlack="9.0" unplanned="false">
          <Notes>
            <Note
              createdBy="Unknown" createdDate="2016-10-09T05:45:21" content={_desc}/>
          </Notes>
        </Task>
'''
    formatted_task = task_xml.lstrip('\n').format(**locals())
    outfile.write(formatted_task)

    children = task.get(CHILDREN, None)
    if children:
        for child in children:
            if isinstance(child, str):
                continue
            else:
                _output_tasks_recursive(outfile, child, level+1)


def _output_tasks(outfile, plan):
    prefix = '''
      <Tasks>
'''
    suffix = '''
      </Tasks>
'''
    outfile.write(prefix.lstrip('\n'))
    _output_tasks_recursive(outfile, plan, 1)
    outfile.write(suffix.lstrip('\n'))


# returns dict(leaf predecessor_id, True) to be used as a set
#
# OWB ignores dependencies on non-leaf tasks; therefore we must
# recursively resolve the dependencies down to leaf nodes.
def _get_leaf_predecessor_ids(id_to_task, predecessor_id, leaf_predecessor_ids):
    def _recursive_resolve(id):
        task = id_to_task[id]
        if has_children(task):
            for child in task[CHILDREN]:
                if isinstance(child, str):
                    continue
                _recursive_resolve(child[ID])
        else:
            leaf_predecessor_ids[id] = True

    _recursive_resolve(predecessor_id)

def _output_dependencies(outfile, id_to_task, deps):
    prefix = '''
      <Dependencies>
'''
    suffix = '''
      </Dependencies>
'''
    outfile.write(prefix.lstrip('\n'))
    for successor_id,predecessor_ids in sorted(deps.items()):
        if has_children(id_to_task[successor_id]):
            continue
        leaf_predecessor_ids = {} # id:True
        for predecessor_id in predecessor_ids.keys():
            _get_leaf_predecessor_ids(id_to_task, predecessor_id, leaf_predecessor_ids)
        for leaf_predecessor_id in sorted(leaf_predecessor_ids.keys()):
            outfile.write('''        <Dependency
          predecessorID="{leaf_predecessor_id}" startFinishType="0" lag="0.0" lagType="0" successorID="{successor_id}"/>
'''.format(**locals()))
    outfile.write(suffix.lstrip('\n'))


def _output_main_file(outfile, plan):
    prefix = '''
<?xml version="1.0"?>
<WORKBENCH_PROJECT>
    <BaseCalendars>
      <Calendar
        name="Standard">
      </Calendar>
    </BaseCalendars>
  <Projects>
    <Project
      UID="AJO44]`-U_```!/5&quot;LU&lt;!```?P```0" closed="false" active="true" approved="false"
      start="2016-10-10T08:00:00" openForTimeEntry="true" format="0" trackMode="0" finish="2016-10-10T08:00:00"
      priority="10" finishImposed="false" cpmType="0" name="Project Plan" startImposed="false"
      program="false">
'''
    suffix = '''
    </Project>
  </Projects>
</WORKBENCH_PROJECT>'''

    # key = ID string, value = task dict
    id_to_task = {}
    sanitize_tasks(plan, id_to_task, add_child_dependencies=True)
    # key = successor, value = {predecessor:True}
    deps = {}
    _validate_tasks(id_to_task, deps)

    outfile.write(prefix.lstrip('\n'))
    _output_tasks(outfile, plan)
    _output_dependencies(outfile, id_to_task, deps)
    outfile.write(suffix.lstrip('\n'))


def plan_to_owb_xml(filename, plan):
    with open(filename, 'wt') as outfile:
        _output_main_file(outfile, plan)

