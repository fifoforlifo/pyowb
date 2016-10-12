from pyowb import *

test1_plan = \
{
    NAME  : 'Test1 Plan',
    CHILDREN  :
    [
        {
            NAME  : 'Buy Stuff',
            CHILDREN :
            [
                SEQUENCE,
                {
                    NAME : 'Buy Flour',
                    EFFORT : 1,
                },
                {
                    ID   : 'buy_chocolate',
                    NAME : 'Buy Chocolate',
                    EFFORT : 3,
                },
                PARALLEL,
                {
                    ID   : 'buy_eggs',
                    NAME : 'Buy Eggs',
                    EFFORT : 5,
                },
                {
                    ID   : 'buy_milk',
                    NAME : 'Buy Milk',
                    EFFORT : 2,
                },
                {
                    ID   : 'buy_tomatoes',
                    NAME : 'Buy Tomatoes',
                    EFFORT : 3,
                },
            ],
        },
        # Declare Lunch before its dependencies to test order-independence.
        # note: this makes the Gantt chart ugly; generally you want to declare things in work-order
        #       to get a nice-looking cascade
        {
            NAME  : 'Lunch',
            CHILDREN :
            [
                {
                    NAME : 'Tomato Soup',
                    DEPS : [ 'buy_tomatoes', 'breakfast' ],
                    EFFORT : 6,
                },
            ],
        },
        {
            ID    : 'breakfast',
            NAME  : 'Breakfast',
            CHILDREN :
            [
                SEQUENCE,
                {
                    NAME : 'Scrambled Eggs',
                    DEPS : [ 'buy_eggs', 'buy_milk' ],
                    EFFORT : 3,
                },
                {
                    NAME : 'Chocolate Milk',
                    DEPS : [ 'buy_chocolate', 'buy_milk' ],
                    EFFORT : 1,
                },
                PARALLEL,
                {
                    NAME : '"Plain" Milk',
                    DEPS : [ 'buy_milk' ],
                    EFFORT : 1,
                },
                {
                    NAME : 'Chocolate Muffins',
                    DEPS : [ 'buy_chocolate', 'buy_milk', 'buy_eggs' ],
                    EFFORT : 8,
                },
            ],
        },
    ],
}

plan_to_owb_xml('test1.xml', test1_plan)
