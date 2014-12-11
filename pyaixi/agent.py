#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines a base class for AIXI-approximate agents.
"""

from __future__ import division
from __future__ import unicode_literals

import copy
import random

from pyaixi import util

# Define a enumeration to represent what type of environment update has been performed.
update_enum = util.enum('action_update', 'percept_update')

# Define some short cuts for ease of reference.
action_update = update_enum.action_update
percept_update = update_enum.percept_update

class Agent:
    """ This base class represents the minimum class elements for a AIXI-style agent.

        The following attributes and methods must be available in all agents, in order
        for the main interaction loop to get responses, give environmental feedback,
        manage learning, and monitor progress:

         - `age`
         - `average_reward()`
         - `generate_random_action()`
         - `last_update`
         - `learning_period`
         - `maximum_action()`
         - `maximum_reward()`
         - `model_size()`
         - `model_update_action()`
         - `model_update_percept()`
         - `search()`
         - `total_reward`
    """

    # Instance methods.

    def __init__(self, environment = None, options = {}):
        """ Construct an AIXI-style learning agent from the given configuration values and the environment.

             - `environment` is an instance of the pyaixi.Environment class that the agent with interact with.
             - `options` is a dictionary of named options and their values.

            The following options are optional:
             - `learning-period`: the number of cycles the agent should learn for.
                                  Defaults to '0', which is indefinite learning.
        """

        # The number of interaction cycles the agent has been alive.
        # Set initially to 0.
        # (Also called `time_cycle` in the C++ version.)
        self.age = 0

        # A reference to the environment the agent interacts with.
        # Set to the environment given. Mandatory.
        # (Called `m_environment` in the C++ version.)
        assert environment is not None, "A non-null environment is required."
        self.environment = environment

        # The type of the last update (action or percept).
        # Set initial to 'action_update'.
        # (Called `m_last_update` in the C++ version.)
        self.last_update = action_update

        # The number of cycles during which the agent learns.
        # Retrieved from the given options under 'learning-period'. Defaults to 0 if not given.
        # (Called `m_learning_period` in the C++ version.)
        self.learning_period = int(options.get('learning-period', 0))

        # Stores the given configuration options.
        # (Called `m_options` in the C++ version.)
        self.options = options

        # The average/mean reward earnt by this agent so far.
        # Set initially to 0.
        self.mean_reward = 0

        # A variable use to accumulate a value used in calculating the standard deviation.
        # Set initially to 0.
        self.reward_m2 = 0

        # The total reward earnt by this agent so far.
        # Set initially to 0.
        # (Called `totalReward` in the C++ version.)
        self.total_reward = 0
    # end def

    def average_reward(self):
        """ Returns the average reward received by the agent at each time step.
            (Called `averageReward` in the C++ version.)
        """

        return self.mean_reward
    # end def

    def generate_random_action(self):
        """ Returns an action generated uniformly at random.
            (Called `genRandomAction` in the C++ version.)
        """

        if hasattr(self.environment, 'valid_actions'):
            return util.choice(self.environment.valid_actions)
        else:
            if hasattr(self.environment, 'minimum_action') and hasattr(self.environment, 'maximum_action'):
                return random.randrange(self.environment.minimum_action(), self.environment.maximum_action())
            # end if
        # end if
    # end def

    def maximum_action(self):
        """ Returns the maximum action the agent can execute.
            (Called `maxAction` in the C++ version.)
        """

        # Get the value from the environment.
        if self.environment is not None:
            return self.environment.maximum_action()
        else:
            return None
        # end if
    # end def

    def maximum_reward(self):
        """ Returns the maximum possible reward the agent can receive in a single cycle.

            (Called `maxReward` in the C++ version.)
        """

        # Get the value from the environment.
        if self.environment is not None:
            return self.environment.maximum_reward()
        else:
            return None
        # end if
    # end def

    def model_size(self):
        """ Returns the size of the agent's model.

            WARNING: this method should be overriden by inheriting classes.

            (Called `modelSize` in the C++ version.)
        """
        return 0
    # end def

    def model_update_action(self, action):
        """ Update the agent's model of the world with an action from the
            environment.

            - `action`: the action that was performed.

            WARNING: this method should be overriden by inheriting classes.

            (Called `modelUpdate` in the C++ version.)
        """

        # The last update must have been a percept, else this action update is invalid.
        assert self.environment.is_valid_action(action), "Invalid action '%s' given." % action
        assert self.last_update == percept_update, "Can only perform an action update after a percept update."

        # Update relevant properties.
        self.age += 1;
        self.last_update = action_update
    # end def

    def model_update_percept(self, observation, reward):
        """ Update the agent's model of the world with a percept from the
            environment.

            - `observation`: the observation that was received.
            - `reward`: the reward that was received.

            WARNING: this method should be overriden by inheriting classes.

            (Called `modelUpdate` in the C++ version.)
        """

        # The last update must have been an action, else this percept update is invalid.
        assert self.last_update == action_update, "Can only perform a percept update after an action update."

        # Update relevant properties.
        self.update_reward_statistics(reward)
        self.last_update = percept_update
    # end def

    def search(self):
        """ Returns the best action for this agent.
        """

        return self.maximum_action()
    # end def

    def reset(self):
        """ Resets the agent.

            NOTE: this method may need to be overriden by inheriting classes,
                  with this method called using `Agent.reset(self)`.
        """
        # Reset the current time cycle, total rewards, and last update action appropriately.
        self.age = 0
        self.mean_reward = 0.0
        self.reward_m2 = 0.0
        self.total_reward = 0.0
        self.last_update = action_update
    # end def

    def update_reward_statistics(self, reward):
        """ Updates the reward statistics with the given reward value.
        """

        # The number of events is the current age plus one, to correct for an off-by-one issue.
        n = self.age + 1

        # Calculate the delta (relative to the old mean) for use in updating M2, which is related to the variance.
        delta = reward - self.mean_reward

        # Update the average/mean reward incrementally.
        self.mean_reward += (delta / n)

        # Update M2, per the Knuth-Welford algorithm for incrementally calculating the variance and standard deviation.
        # See: http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Online_algorithm
        self.reward_m2 += delta * (reward - self.mean_reward)

        # Update the total reward.
        self.total_reward += reward
    # end def
# end class