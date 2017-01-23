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

# Returns id_to_intid: dict(task_id, int_id)
def _generate_integer_ids(id_to_task):
    intid = 0
    id_to_intid = {}
    for task_id in sorted(id_to_task.keys()):
        id_to_intid[task_id] = intid
        intid += 1
    return id_to_intid

def _date_as_lp_string(date):
    return date.strftime('%Y-%m-%dT%H:%M:%S')

def _effort_as_lp_string(effort_in_days):
    hours = int(effort_in_days * 8)
    minutes = int((effort_in_days * 8 * 60) % 60)
    seconds = 0
    return 'PT{hours}H{minutes}M{seconds}S'.format(**locals())

# returns dict(leaf predecessor_id, True) to be used as a set
#
# LP ignores dependencies on non-leaf tasks; therefore we must
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


def _output_tasks_recursive(outfile, deps, id_to_task, id_to_intid, task, level):
    effort_in_days = task.get(EFFORT, 0)

    _category = parse_category(task[NAME])
    _name = xml_escape_elem(task[NAME])
    _id = xml_escape_elem(task[ID])
    _intid = id_to_intid[task[ID]]
    if DESC in task:
        _desc = '            <Notes>{0}</Notes>\n'.format(xml_escape_elem(task.get(DESC, ' ')))
    else:
        _desc = ''
    _level = level
    _summary = 1 if has_children(task) else 0
    _start_date = _date_as_lp_string(_global_start_date)
    _end_date = _date_as_lp_string(_global_start_date + timedelta(days=effort_in_days))
    _duration = _effort_as_lp_string(effort_in_days)
    _estimated = EFFORT in task

    task_xml_prefix = '''
        <Task>
            <UID>{_intid}</UID>
            <ID>{_id}</ID>
            <Name>{_name}</Name>
            <Type>0</Type>
            <IsNull>0</IsNull>
            <CreateDate>2017-01-22T21:35:00</CreateDate>
            <WBS></WBS>
            <OutlineNumber>1</OutlineNumber>
            <OutlineLevel>{_level}</OutlineLevel>
            <Priority>500</Priority>
            <Start>{_start_date}</Start>
            <!--Finish>{_end_date}</Finish-->
            <Duration>{_duration}</Duration>
            <DurationFormat>39</DurationFormat>
            <ResumeValid>0</ResumeValid>
            <EffortDriven>1</EffortDriven>
            <Recurring>0</Recurring>
            <OverAllocated>0</OverAllocated>
            <Estimated>{_estimated}</Estimated>
            <Milestone>0</Milestone>
            <Summary>{_summary}</Summary>
            <Critical>0</Critical>
            <IsSubproject>0</IsSubproject>
            <IsSubprojectReadOnly>0</IsSubprojectReadOnly>
            <ExternalTask>0</ExternalTask>
            <FixedCostAccrual>2</FixedCostAccrual>
            <RemainingDuration>{_duration}</RemainingDuration>
            <ConstraintType>0</ConstraintType>
            <CalendarUID>-1</CalendarUID>
            <ConstraintDate>1970-01-01T00:00:00</ConstraintDate>
            <LevelAssignments>0</LevelAssignments>
            <LevelingCanSplit>0</LevelingCanSplit>
            <LevelingDelay>0</LevelingDelay>
            <LevelingDelayFormat>7</LevelingDelayFormat>
            <IgnoreResourceCalendar>0</IgnoreResourceCalendar>{_desc}
            <HideBar>0</HideBar>
            <Rollup>0</Rollup>
            <EarnedValueMethod>0</EarnedValueMethod>
'''
    task_xml_suffix = '''
            <Active>1</Active>
            <Manual>0</Manual>
        </Task>
'''
    predecessor_xml = '''
            <PredecessorLink>
                <PredecessorUID>{_predecessor_intid}</PredecessorUID>
                <Type>1</Type>
                <CrossProject>0</CrossProject>
            </PredecessorLink>
'''

    predecessor_ids = deps.get(task[ID], {})
    leaf_predecessor_ids = {} # id:True
    for predecessor_id in predecessor_ids.keys():
        _get_leaf_predecessor_ids(id_to_task, predecessor_id, leaf_predecessor_ids)    

    outfile.write(task_xml_prefix.lstrip('\n').format(**locals()))
    for leaf_predecessor_id in sorted(leaf_predecessor_ids.keys()):
        _predecessor_intid = id_to_intid[leaf_predecessor_id]
        outfile.write(predecessor_xml.lstrip('\n').format(**locals()))
    outfile.write(task_xml_suffix.lstrip('\n'))

    children = task.get(CHILDREN, None)
    if children:
        for child in children:
            if isinstance(child, str):
                continue
            else:
                _output_tasks_recursive(outfile, deps, id_to_task, id_to_intid, child, level+1)


def _output_tasks(outfile, deps, id_to_task, id_to_intid, plan):
    prefix = '''
      <Tasks>
'''
    suffix = '''
      </Tasks>
'''
    outfile.write(prefix.lstrip('\n'))
    _output_tasks_recursive(outfile, deps, id_to_task, id_to_intid, plan, 1)
    outfile.write(suffix.lstrip('\n'))


def _output_main_file(outfile, plan):
    prefix = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Project xmlns="http://schemas.microsoft.com/project">
    <SaveVersion>9</SaveVersion>
    <Name>TestHierarchy</Name>
    <Title>TestHierarchy</Title>
    <Manager></Manager>
    <ScheduleFromStart>1</ScheduleFromStart>
    <StartDate>2017-01-23T08:00:00</StartDate>
    <FinishDate>2017-02-08T17:00:00</FinishDate>
    <FYStartDate>1</FYStartDate>
    <CriticalSlackLimit>0</CriticalSlackLimit>
    <CurrencyDigits>2</CurrencyDigits>
    <CurrencySymbol>$</CurrencySymbol>
    <CurrencySymbolPosition>0</CurrencySymbolPosition>
    <CalendarUID>1</CalendarUID>
    <DefaultStartTime>02:00:00</DefaultStartTime>
    <DefaultFinishTime>11:00:00</DefaultFinishTime>
    <MinutesPerDay>480</MinutesPerDay>
    <MinutesPerWeek>2400</MinutesPerWeek>
    <DaysPerMonth>20</DaysPerMonth>
    <DefaultTaskType>0</DefaultTaskType>
    <DefaultFixedCostAccrual>2</DefaultFixedCostAccrual>
    <DefaultStandardRate>10</DefaultStandardRate>
    <DefaultOvertimeRate>15</DefaultOvertimeRate>
    <DurationFormat>7</DurationFormat>
    <WorkFormat>2</WorkFormat>
    <EditableActualCosts>0</EditableActualCosts>
    <HonorConstraints>0</HonorConstraints>
    <EarnedValueMethod>0</EarnedValueMethod>
    <InsertedProjectsLikeSummary>0</InsertedProjectsLikeSummary>
    <MultipleCriticalPaths>0</MultipleCriticalPaths>
    <NewTasksEffortDriven>0</NewTasksEffortDriven>
    <NewTasksEstimated>1</NewTasksEstimated>
    <SplitsInProgressTasks>0</SplitsInProgressTasks>
    <SpreadActualCost>0</SpreadActualCost>
    <SpreadPercentComplete>0</SpreadPercentComplete>
    <TaskUpdatesResource>1</TaskUpdatesResource>
    <FiscalYearStart>0</FiscalYearStart>
    <WeekStartDay>1</WeekStartDay>
    <MoveCompletedEndsBack>0</MoveCompletedEndsBack>
    <MoveRemainingStartsBack>0</MoveRemainingStartsBack>
    <MoveRemainingStartsForward>0</MoveRemainingStartsForward>
    <MoveCompletedEndsForward>0</MoveCompletedEndsForward>
    <BaselineForEarnedValue>0</BaselineForEarnedValue>
    <AutoAddNewResourcesAndTasks>1</AutoAddNewResourcesAndTasks>
    <CurrentDate>2017-01-22T21:43:00</CurrentDate>
    <MicrosoftProjectServerURL>1</MicrosoftProjectServerURL>
    <Autolink>1</Autolink>
    <NewTaskStartDate>0</NewTaskStartDate>
    <DefaultTaskEVMethod>0</DefaultTaskEVMethod>
    <ProjectExternallyEdited>0</ProjectExternallyEdited>
    <ActualsInSync>0</ActualsInSync>
    <RemoveFileProperties>0</RemoveFileProperties>
    <AdminProject>0</AdminProject>
    <ExtendedAttributes/>
    <Calendars>
        <Calendar>
            <UID>1</UID>
            <Name>Standard</Name>
            <IsBaseCalendar>1</IsBaseCalendar>
            <WeekDays>
                <WeekDay>
                    <DayType>1</DayType>
                    <DayWorking>0</DayWorking>
                </WeekDay>
                <WeekDay>
                    <DayType>2</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>08:00:00</FromTime>
                            <ToTime>12:00:00</ToTime>
                        </WorkingTime>
                        <WorkingTime>
                            <FromTime>13:00:00</FromTime>
                            <ToTime>17:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>3</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>08:00:00</FromTime>
                            <ToTime>12:00:00</ToTime>
                        </WorkingTime>
                        <WorkingTime>
                            <FromTime>13:00:00</FromTime>
                            <ToTime>17:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>4</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>08:00:00</FromTime>
                            <ToTime>12:00:00</ToTime>
                        </WorkingTime>
                        <WorkingTime>
                            <FromTime>13:00:00</FromTime>
                            <ToTime>17:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>5</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>08:00:00</FromTime>
                            <ToTime>12:00:00</ToTime>
                        </WorkingTime>
                        <WorkingTime>
                            <FromTime>13:00:00</FromTime>
                            <ToTime>17:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>6</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>08:00:00</FromTime>
                            <ToTime>12:00:00</ToTime>
                        </WorkingTime>
                        <WorkingTime>
                            <FromTime>13:00:00</FromTime>
                            <ToTime>17:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>7</DayType>
                    <DayWorking>0</DayWorking>
                </WeekDay>
            </WeekDays>
        </Calendar>
        <Calendar>
            <UID>2</UID>
            <Name>24 Hours</Name>
            <IsBaseCalendar>1</IsBaseCalendar>
            <WeekDays>
                <WeekDay>
                    <DayType>1</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>00:00:00</FromTime>
                            <ToTime>00:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>2</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>00:00:00</FromTime>
                            <ToTime>00:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>3</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>00:00:00</FromTime>
                            <ToTime>00:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>4</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>00:00:00</FromTime>
                            <ToTime>00:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>5</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>00:00:00</FromTime>
                            <ToTime>00:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>6</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>00:00:00</FromTime>
                            <ToTime>00:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>7</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>00:00:00</FromTime>
                            <ToTime>00:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
            </WeekDays>
        </Calendar>
        <Calendar>
            <UID>3</UID>
            <Name>Night Shift</Name>
            <IsBaseCalendar>1</IsBaseCalendar>
            <WeekDays>
                <WeekDay>
                    <DayType>1</DayType>
                    <DayWorking>0</DayWorking>
                </WeekDay>
                <WeekDay>
                    <DayType>2</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>23:00:00</FromTime>
                            <ToTime>00:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>3</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>00:00:00</FromTime>
                            <ToTime>03:00:00</ToTime>
                        </WorkingTime>
                        <WorkingTime>
                            <FromTime>04:00:00</FromTime>
                            <ToTime>08:00:00</ToTime>
                        </WorkingTime>
                        <WorkingTime>
                            <FromTime>23:00:00</FromTime>
                            <ToTime>00:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>4</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>00:00:00</FromTime>
                            <ToTime>03:00:00</ToTime>
                        </WorkingTime>
                        <WorkingTime>
                            <FromTime>04:00:00</FromTime>
                            <ToTime>08:00:00</ToTime>
                        </WorkingTime>
                        <WorkingTime>
                            <FromTime>23:00:00</FromTime>
                            <ToTime>00:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>5</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>00:00:00</FromTime>
                            <ToTime>03:00:00</ToTime>
                        </WorkingTime>
                        <WorkingTime>
                            <FromTime>04:00:00</FromTime>
                            <ToTime>08:00:00</ToTime>
                        </WorkingTime>
                        <WorkingTime>
                            <FromTime>23:00:00</FromTime>
                            <ToTime>00:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>6</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>00:00:00</FromTime>
                            <ToTime>03:00:00</ToTime>
                        </WorkingTime>
                        <WorkingTime>
                            <FromTime>04:00:00</FromTime>
                            <ToTime>08:00:00</ToTime>
                        </WorkingTime>
                        <WorkingTime>
                            <FromTime>23:00:00</FromTime>
                            <ToTime>00:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
                <WeekDay>
                    <DayType>7</DayType>
                    <DayWorking>1</DayWorking>
                    <WorkingTimes>
                        <WorkingTime>
                            <FromTime>00:00:00</FromTime>
                            <ToTime>03:00:00</ToTime>
                        </WorkingTime>
                        <WorkingTime>
                            <FromTime>04:00:00</FromTime>
                            <ToTime>08:00:00</ToTime>
                        </WorkingTime>
                    </WorkingTimes>
                </WeekDay>
            </WeekDays>
        </Calendar>
    </Calendars>
'''
    suffix = '''
    <Resources>
        <Resource>
            <UID>0</UID>
            <ID>0</ID>
            <Name>Unassigned</Name>
            <Type>1</Type>
            <IsNull>0</IsNull>
            <Initials>U</Initials>
            <Group></Group>
            <EmailAddress></EmailAddress>
            <MaxUnits>1</MaxUnits>
            <PeakUnits>1</PeakUnits>
            <OverAllocated>0</OverAllocated>
            <Start>2017-01-23T08:00:00</Start>
            <Finish>2017-02-08T17:00:00</Finish>
            <CanLevel>0</CanLevel>
            <AccrueAt>3</AccrueAt>
            <StandardRateFormat>3</StandardRateFormat>
            <OvertimeRateFormat>3</OvertimeRateFormat>
            <IsGeneric>0</IsGeneric>
            <IsInactive>0</IsInactive>
            <IsEnterprise>0</IsEnterprise>
            <IsBudget>0</IsBudget>
            <AvailabilityPeriods/>
        </Resource>
    </Resources>
    <Assignments>
    </Assignments>
</Project>
'''

    # key = ID string, value = task dict
    id_to_task = {}
    sanitize_tasks(plan, id_to_task, add_child_dependencies=False)
    # key = successor, value = {predecessor:True}
    deps = {}
    _validate_tasks(id_to_task, deps)
    # key = task_id, value = intid
    id_to_intid = _generate_integer_ids(id_to_task)

    outfile.write(prefix.lstrip('\n'))
    _output_tasks(outfile, deps, id_to_task, id_to_intid, plan)
    outfile.write(suffix.lstrip('\n'))


def plan_to_project_libre_xml(filename, plan, start_date=None):
    global _global_start_date
    if start_date:
        _global_start_date = start_date
    else:
        _global_start_date = datetime.now()

    with open(filename, 'wt') as outfile:
        _output_main_file(outfile, plan)

