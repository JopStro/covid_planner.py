"""
Tests for the covid_planner module
"""
import covid_planner
import time


def test_alarms():
    """
    Tests setting, getting and deleting alarms
    """
    main.set_alarm('2030-01-01T10:00', 'test', 'true', '')
    main.set_alarm('wkijdowi', 'wrong', 'test', '')


    assert main.get_alarms() == [{'title': 'test', 'content': 'Set to go off at 10:00 on 01/01/2030'}]

    main.del_alarm('test')
    assert main.s.empty() == True

def test_notifs():
    """
    Tests adding and removing notifications
    """
    main.add_notif('Nice', 'Very Nice')
    main.add_notif('Hello', 'World')
    
    assert main.notifs == [{'title': 'Hello', 'content': 'World'}, {'title': 'Nice', 'content': 'Very Nice'}]

    main.del_notif('Nice')
    assert main.notifs == [{'title': 'Hello', 'content': 'World'}]
    
    # Attempt to add repeat notifications.
    main.add_notif('Nice', 'Very Nice')
    main.add_notif('Hello', 'World')
    assert main.notifs == [{'title': 'Hello', 'content': 'World'}]
