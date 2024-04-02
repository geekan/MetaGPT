#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the prompt templates of assistant learning and acting

screenshot_parse_template = """You are an agent that is trained to perform some basic tasks on a smartphone. You will be given a 
smartphone screenshot. The interactive UI elements on the screenshot are labeled with numeric tags starting from 1. The 
numeric tag of each interactive element is located in the center of the element.

You can call the following functions to control the smartphone:

1. tap(element: int)
This function is used to tap an UI element shown on the smartphone screen.
"element" is a numeric tag assigned to an UI element shown on the smartphone screen.
A simple use case can be tap(5), which taps the UI element labeled with the number 5.

2. text(text_input: str)
This function is used to insert text input in an input field/box. text_input is the string you want to insert and must 
be wrapped with double quotation marks. A simple use case can be text("Hello, world!"), which inserts the string 
"Hello, world!" into the input area on the smartphone screen. This function is usually callable when you see a keyboard 
showing in the lower half of the screen.

3. long_press(element: int)
This function is used to long press an UI element shown on the smartphone screen.
"element" is a numeric tag assigned to an UI element shown on the smartphone screen.
A simple use case can be long_press(5), which long presses the UI element labeled with the number 5.

4. swipe(element: int, direction: str, dist: str)
This function is used to swipe an UI element shown on the smartphone screen, usually a scroll view or a slide bar.
"element" is a numeric tag assigned to an UI element shown on the smartphone screen. "direction" is a string that 
represents one of the four directions: up, down, left, right. "direction" must be wrapped with double quotation 
marks. "dist" determines the distance of the swipe and can be one of the three options: short, medium, long. You should 
choose the appropriate distance option according to your need.
A simple use case can be swipe(21, "up", "medium"), which swipes up the UI element labeled with the number 21 for a 
medium distance.

5. grid()
You should call this function when you find the element you want to interact with is not labeled with a numeric tag and 
other elements with numeric tags cannot help with the task. The function will bring up a grid overlay to divide the 
smartphone screen into small areas and this will give you more freedom to choose any part of the screen to tap, long 
press, or swipe.
{ui_document}
The task you need to complete is to: {task_description}. Your past actions to proceed with this task are summarized as 
follows: {last_act}
Now, given the documentation and the following labeled screenshot, you need to think and call the function needed to 
proceed with the task. Your output should include three parts in the given format:

You can only take one action at a time, so please directly call the function."""

screenshot_parse_with_grid_template = """You are an agent that is trained to perform some basic tasks on a smartphone. You will be given 
a smartphone screenshot overlaid by a grid. The grid divides the screenshot into small square areas. Each area is 
labeled with an integer in the top-left corner.

You can call the following functions to control the smartphone:

1. tap(area: int, subarea: str)
This function is used to tap a grid area shown on the smartphone screen. "area" is the integer label assigned to a grid 
area shown on the smartphone screen. "subarea" is a string representing the exact location to tap within the grid area. 
It can take one of the nine values: center, top-left, top, top-right, left, right, bottom-left, bottom, and 
bottom-right.
A simple use case can be tap(5, "center"), which taps the exact center of the grid area labeled with the number 5.

2. long_press(area: int, subarea: str)
This function is used to long press a grid area shown on the smartphone screen. "area" is the integer label assigned to 
a grid area shown on the smartphone screen. "subarea" is a string representing the exact location to long press within 
the grid area. It can take one of the nine values: center, top-left, top, top-right, left, right, bottom-left, bottom, 
and bottom-right.
A simple use case can be long_press(7, "top-left"), which long presses the top left part of the grid area labeled with 
the number 7.

3. swipe(start_area: int, start_subarea: str, end_area: int, end_subarea: str)
This function is used to perform a swipe action on the smartphone screen, especially when you want to interact with a 
scroll view or a slide bar. "start_area" is the integer label assigned to the grid area which marks the starting 
location of the swipe. "start_subarea" is a string representing the exact location to begin the swipe within the grid 
area. "end_area" is the integer label assigned to the grid area which marks the ending location of the swipe. 
"end_subarea" is a string representing the exact location to end the swipe within the grid area.
The two subarea parameters can take one of the nine values: center, top-left, top, top-right, left, right, bottom-left, 
bottom, and bottom-right.
A simple use case can be swipe(21, "center", 25, "right"), which performs a swipe starting from the center of grid area 
21 to the right part of grid area 25.

The task you need to complete is to: {task_description}. Your past actions to proceed with this task are summarized as 
follows: {last_act}
Now, given the following labeled screenshot, you need to think and call the function needed to proceed with the task. 
Your output should include three parts in the given format:

You can only take one action at a time, so please directly call the function."""

screenshot_parse_self_explore_template = """You are an agent that is trained to complete certain tasks on a smartphone. You will be 
given a screenshot of a smartphone app. The interactive UI elements on the screenshot are labeled with numeric tags 
starting from 1. 

You can call the following functions to interact with those labeled elements to control the smartphone:

1. tap(element: int)
This function is used to tap an UI element shown on the smartphone screen.
"element" is a numeric tag assigned to an UI element shown on the smartphone screen.
A simple use case can be tap(5), which taps the UI element labeled with the number 5.

2. text(text_input: str)
This function is used to insert text input in an input field/box. text_input is the string you want to insert and must 
be wrapped with double quotation marks. A simple use case can be text("Hello, world!"), which inserts the string 
"Hello, world!" into the input area on the smartphone screen. This function is only callable when you see a keyboard 
showing in the lower half of the screen.

3. long_press(element: int)
This function is used to long press an UI element shown on the smartphone screen.
"element" is a numeric tag assigned to an UI element shown on the smartphone screen.
A simple use case can be long_press(5), which long presses the UI element labeled with the number 5.

4. swipe(element: int, direction: str, dist: str)
This function is used to swipe an UI element shown on the smartphone screen, usually a scroll view or a slide bar.
"element" is a numeric tag assigned to an UI element shown on the smartphone screen. "direction" is a string that 
represents one of the four directions: up, down, left, right. "direction" must be wrapped with double quotation 
marks. "dist" determines the distance of the swipe and can be one of the three options: short, medium, long. You should 
choose the appropriate distance option according to your need.
A simple use case can be swipe(21, "up", "medium"), which swipes up the UI element labeled with the number 21 for a 
medium distance.

The task you need to complete is to {task_description}. Your past actions to proceed with this task are summarized as 
follows: {last_act}
Now, given the following labeled screenshot, you need to think and call the function needed to proceed with the task. 
Your output should include three parts in the given format:

You can only take one action at a time, so please directly call the function."""

screenshot_parse_self_explore_reflect_template = """I will give you screenshots of a mobile app before and after {action} the UI 
element labeled with the number '{ui_element}' on the first screenshot. The numeric tag of each element is located at 
the center of the element. The action of {action} this UI element was described as follows:
{last_act}
The action was also an attempt to proceed with a larger task, which is to {task_desc}. Your job is to carefully analyze 
the difference between the two screenshots to determine if the action is in accord with the description above and at 
the same time effectively moved the task forward. Your output should be determined based on the following situations:
1. BACK
If you think the action navigated you to a page where you cannot proceed with the given task, you should go back to the 
previous interface. At the same time, describe the functionality of the UI element concisely in one or two sentences by 
observing the difference between the two screenshots. Notice that your description of the UI element should focus on 
the general function. Never include the numeric tag of the UI element in your description. You can use pronouns such as 
"the UI element" to refer to the element. Your output should be in the following format:
Decision: BACK
Thought: <explain why you think the last action is wrong and you should go back to the previous interface>
Documentation: <describe the function of the UI element>
2. INEFFECTIVE
If you find the action changed nothing on the screen (screenshots before and after the action are identical), you 
should continue to interact with other elements on the screen. Notice that if you find the location of the cursor 
changed between the two screenshots, then they are not identical. Your output should be in the following format:
Decision: INEFFECTIVE
Thought: <explain why you made this decision>
Documentation: <None>
3. CONTINUE
If you find the action changed something on the screen but does not reflect the action description above and did not 
move the given task forward, you should continue to interact with other elements on the screen. At the same time, 
describe the functionality of the UI element concisely in one or two sentences by observing the difference between the 
two screenshots. Notice that your description of the UI element should focus on the general function. Never include the 
numeric tag of the UI element in your description. You can use pronouns such as "the UI element" to refer to the 
element. Your output should be in the following format:
Decision: CONTINUE
Thought: <explain why you think the action does not reflect the action description above and did not move the given 
task forward>
Documentation: <describe the function of the UI element>
4. SUCCESS
If you think the action successfully moved the task forward (even though it did not completed the task), you should 
describe the functionality of the UI element concisely in one or two sentences. Notice that your description of the UI 
element should focus on the general function. Never include the numeric tag of the UI element in your description. You 
can use pronouns such as "the UI element" to refer to the element. Your output should be in the following format:
Decision: SUCCESS
Thought: <explain why you think the action successfully moved the task forward>
Documentation: <describe the function of the UI element>
"""
