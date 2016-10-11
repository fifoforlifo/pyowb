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
                    COST : 1.1,
                },
                {
                    ID   : 'buy_chocolate',
                    NAME : 'Buy Chocolate',
                    COST : 1.2,
                },
                PARALLEL,
                {
                    ID   : 'buy_eggs',
                    NAME : 'Buy Eggs',
                    COST : 2,
                },
                {
                    ID   : 'buy_milk',
                    NAME : 'Buy Milk',
                    COST : 3,
                },
            ],
        },
        {
            NAME  : 'Breakfast',
            CHILDREN :
            [
                SEQUENCE,
                {
                    NAME : 'Scrambled Eggs',
                    DEPS : [ 'buy_eggs', 'buy_milk' ],
                    COST : 3,
                },
                {
                    NAME : 'Chocolate Milk',
                    DEPS : [ 'buy_chocolate', 'buy_milk' ],
                    COST : 0.5,
                },
                PARALLEL,
                {
                    NAME : 'Choco Muffins',
                    DEPS : [ 'buy_chocolate', 'buy_milk', 'buy_eggs' ],
                    COST : 8,
                },
            ],
        }
    ],
}

plan_to_owb_xml('test1.xml', test1_plan)
