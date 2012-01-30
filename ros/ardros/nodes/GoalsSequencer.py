#!/usr/bin/env python
'''
Created January, 2012

@author: Dr. Rainer Hessmer

  DriveToGoals.py - This ROS nodes reads a sequence of goals from a text file
  and then commands a robot running the ROS navigation stack to navigate to the
  goals in sequence.

  Copyright (c) 2012 Dr. Rainer Hessmer.  All right reserved.

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are met:
      * Redistributions of source code must retain the above copyright
        notice, this list of conditions and the following disclaimer.
      * Redistributions in binary form must reproduce the above copyright
        notice, this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.
      * Neither the name of the Vanadium Labs LLC nor the names of its 
        contributors may be used to endorse or promote products derived 
        from this software without specific prior written permission.
  
  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
  DISCLAIMED. IN NO EVENT SHALL VANADIUM LABS BE LIABLE FOR ANY DIRECT, INDIRECT,
  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
  OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
  OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import roslib; roslib.load_manifest('ardros')
import rospy
import tf
import math
from math import sin, cos, pi
import sys

# Brings in the SimpleActionClient
import actionlib
from move_base_msgs.msg import MoveBaseAction
from move_base_msgs.msg import MoveBaseGoal
from actionlib_msgs.msg import GoalStatus
from geometry_msgs.msg import Quaternion



class GoalsFileParser(object):
	'''
	Helper class for extracting goals from a text file. Here is a sample file content:

	// End of first hall way leg
	x = 0.705669820309, y = 3.92879199982, theta = -0.712161728691
	x = 2.3, y = 0.4, theta = 1.1

	'''

	def Parse(self, filePath):
		'''
		Parses the specified file and returns the found goal poses as an array of
		(x,y,theta) tuples.
		'''
		self._GoalsFilePath = filePath
		file = open(filePath, 'r')
		goals = []
		for line in file:
			goal = self._ParseLine(line)
			if goal is not None:
				goals.append(goal)
		
		return goals

	def _ParseLine(self, line):
		trimmedLine = line.strip()
		if trimmedLine.startswith('//'):
			# we are dealing with a comment line
			return
		if len(trimmedLine) == 0:
			# we are dealing with an empty line
			return
		
		#print(trimmedLine)
		lineParts = trimmedLine.split(',')
		x = self._ExtractValue('x', lineParts[0])
		y = self._ExtractValue('y', lineParts[1])
		theta = self._ExtractValue('theta', lineParts[2])
		
		goal = (x, y, theta)
		return goal
	
	def _ExtractValue(self, variableName, linePart):
		'''
		Takes as input text like this:
		x = 0.73444
		
		Checks that the specified variableName matches the name of the variable in the string.
		then extracts the float value of the '=' sign
		
		'''

		nameValueParts = linePart.split('=')
		if nameValueParts[0].strip() != variableName:
			raise NameError('Expected variable name ' + variableName + ' but found ' + nameValueParts[0].strip())

		return float(nameValueParts[1].strip())


class GoalsSequencer(object):
	'''
	'''
	
	def __init__(self, goalFrameId = '/map'):
		self._GoalFrameId = goalFrameId
		
		# Initializes a rospy node so that the SimpleActionClient can publish and subscribe over ROS.
		rospy.init_node('goalsSequencer')
		
		self._Client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
		# Waits until the action server has started up and started listening for goals.
		self._Client.wait_for_server()

	def NavigateToGoals(self, goals):
		for goal in goals:
			print("Navigating to goal " + str(goal))
			self._NavigateToGoal(goal)
		
	def _NavigateToGoal(self, goal):
		moveBaseGoal = self._CreateMoveBaseGoal(goal)
		
		self._Client.send_goal(moveBaseGoal)
		self._Client.wait_for_result()
		if self._Client.get_state() == GoalStatus.SUCCEEDED:
			rospy.loginfo("Goal reached")
		else:
			rospy.logerr("Could not execute goal for some reason")

	def _CreateMoveBaseGoal(self, goal):
		'''
		Creates an instance of MoveBaseGoal based on a simple goal in the form of a (x,y,theta) tuple
		'''
		
		x,y,theta = goal
		
		moveBaseGoal = MoveBaseGoal()
		moveBaseGoal.target_pose.header.frame_id = self._GoalFrameId
		moveBaseGoal.target_pose.header.stamp = rospy.Time.now()

		moveBaseGoal.target_pose.pose.position.x = x
		moveBaseGoal.target_pose.pose.position.y = y
		
		quaternionArray = tf.transformations.quaternion_about_axis(theta, (0,0,1))
		# quaternion_about_axis offers a convenient way for calculating the members of a quaternion.
		# In order to use it we need to convert it to a Quaternion message structure
		moveBaseGoal.target_pose.pose.orientation = self.array_to_quaternion(quaternionArray)

		print(moveBaseGoal)
		return moveBaseGoal

	def array_to_quaternion(self, nparr):
		'''
		Takes a numpy array holding the members of a quaternion and returns it as a 
		geometry_msgs.msg.Quaternion message instance.
		'''
		quat = Quaternion()
		quat.x = nparr[0]
		quat.y = nparr[1]
		quat.z = nparr[2]
		quat.w = nparr[3]
		return quat

if __name__ == '__main__':
	
	goalsFilePath = "./nodes/goals.txt"
	if (len(sys.argv) > 1):
		# we accept the path to the goals text file as a command line argument
		goalsFilePath = sys.argv[1]

	goalsFileParser = GoalsFileParser()
	goals = goalsFileParser.Parse(goalsFilePath)
	print(goals)

	goalsSequencer = GoalsSequencer(goalFrameId = '/map')
	goalsSequencer.NavigateToGoals(goals)
	
	
	