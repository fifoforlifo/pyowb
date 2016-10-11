# Python plan -> Open Workbench XML converter.
#
#   Python plan defines a Work Breakdown Structure where
#   tasks are dictionaries and children are defined in a list.
#   Children can contain sequences, to simplify data input;
#   sequenced tasks are automatically chained (dependencies).

ID = 'id'
NAME = 'name'
DESC = 'desc'
DEPS = 'deps'
COST = 'cost'
CHILDREN = 'children'
SEQUENCE = 'sequence'
PARALLEL = 'parallel'

global_auto_id = 100
def next_global_auto_id():
    global global_auto_id, global_unique_suffix
    auto_id = '_auto' + str(global_auto_id)
    global_auto_id += 1
    return auto_id

def insert_dependency(deps, successor, predecessor):
    if successor not in deps:
        deps[successor] = {}
    deps[successor][predecessor] = True


def _xml_escape(string):
    return string.replace('&', '&amp;')
    
def _output_tasks_recursive(outfile, deps, task, level, auto_predecessor_id=None):
    if ID not in task:
        task[ID] = next_global_auto_id()

    # TODO: add all deps
    if auto_predecessor_id:
        insert_dependency(deps, task[ID], auto_predecessor_id)
    if DEPS in task:
        for predecessor_id in task[DEPS]:
            insert_dependency(deps, task[ID], predecessor_id)

    task_xml = '''
        <Task
          category="drv" start="2016-10-10T08:00:00" finish="2016-10-12T17:00:00"
          proxy="false"
          critical="false" status="0" outlineLevel="{_level}" summary="{_summary}"
          milestone="false" name="{_name}" taskID="{_id}" fixed="false"
          locked="false" key="false" percComp="0.0" totalSlack="9.0" unplanned="false">
          <Notes>
            <Note
              createdBy="Unknown" createdDate="2016-10-09T05:45:21" content="{_desc}"/>
          </Notes>
        </Task>
'''

    is_summary = 'true' if (CHILDREN in task) and (len(task[CHILDREN]) != 0) else 'false'

    formatted_task = task_xml.lstrip('\n').format(
        _name = _xml_escape(task[NAME]),
        _id = _xml_escape(task[ID]),
        _desc = _xml_escape(task.get(DESC, ' ')),
        _level = level,
        _summary = is_summary,
    )
    outfile.write(formatted_task)

    children = task.get(CHILDREN, None)
    if children:
        auto_predecessor_id = None
        in_sequence = False
        for child in children:
            if child == SEQUENCE:
                auto_predecessor_id = None
                in_sequence = True
            elif child == PARALLEL:
                auto_predecessor_id = None
                in_sequence = False
            else:
                _output_tasks_recursive(outfile, deps, child, level+1, auto_predecessor_id)
                if in_sequence:
                    auto_predecessor_id = child[ID]


def _output_tasks(outfile, deps, plan):
    prefix = '''
      <Tasks>
'''
    suffix = '''
      </Tasks>
'''
    outfile.write(prefix.lstrip('\n'))
    _output_tasks_recursive(outfile, deps, plan, 1)
    outfile.write(suffix.lstrip('\n'))


def _output_dependencies(outfile, deps):
    prefix = '''
      <Dependencies>
'''
    suffix = '''
      </Dependencies>
'''
    outfile.write(prefix.lstrip('\n'))
    for successor_id,predecessor_ids in deps.items():
        for predecessor_id,_ in predecessor_ids.items():
            outfile.write('''        <Dependency
          predecessorID="{predecessor_id}" startFinishType="0" lag="0.0" lagType="0" successorID="{successor_id}"/>
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

    # key = successor, rhs = {predecessor:True}
    deps = {}

    outfile.write(prefix.lstrip('\n'))
    _output_tasks(outfile, deps, plan)
    _output_dependencies(outfile, deps)
    outfile.write(suffix.lstrip('\n'))


def plan_to_owb_xml(filename, plan):
    with open(filename, 'wt') as outfile:
        _output_main_file(outfile, plan)

