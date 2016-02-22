import requests
import json
import os
import pprint
import pymongo
import string
import re
import hearthapi


""" The parent class from which all other cards inherit. """
class Card:
	# These attributes are common to all cards.
	name = ""
	set_id = ""
	cost = 0
	mechanics = []
	card_text = ""
	player_class = ""

	def __init__(self):
		return

""" Inherits from Card. """
class Minion (Card):
	attack = 0
	health = 1
	race = ""

	# Loads data from a dictionary of attributes.
	# Number values have to be converted from string to integer.
	def __init__(self, m_dict):
		try:
			self.name = m_dict["name"]
			self.set_id = m_dict["id"]
			self.attack = int(m_dict["attack"]) # Can return ValueError
			self.health = int(m_dict["health"]) # Can return ValueError
			self.cost = int(m_dict["cost"])		# Can return ValueError
			self.card_text = m_dict["text"]
		except Exception as e:
			print "Exception caught at {}".format(e)

		# The minion may not be affiliated with a race or class, but check anyway.
		if "race" in m_dict.keys():
			self.race = m_dict["race"]
		if "playerClass" in m_dict.keys():
			self.player_class = m_dict["playerClass"]
		else:
			self.player_class = "NEUTRAL"
		return

	# Returns a string of the form:
	# (COST): NAME (ATK/DEF)
	def __str__(self):
		output = "({}): {} ".format(self.cost, self.name)
		output += "({}/{})".format(self.attack, self.health)
		return output

""" Inherits from Card. """
class Weapon (Card):
	durability = 1
	power = 1

	def __init__(self, m_dict):
		try:
			self.name = m_dict["name"]
			self.set_id = m_dict["id"]
			self.power = int(m_dict["attack"])
			self.durability = int(m_dict["durability"])
			self.cost = int(m_dict["cost"])
		except Exception as e:
			print "Exception caught at ", e
		# Weapon may not have any text or mechanics
		if "text" in m_dict.keys():
			self.card_text = m_dict["text"]
		if "mechanics" in m_dict.keys():
			self.mechanics = m_dict["mechanics"]
		# Currently no generic weapons exist, but let's leave the possibility open
		if "playerClass" in m_dict.keys():
			self.player_class = m_dict["playerClass"]
		else:
			self.player_class = "NEUTRAL"
		return

	def __str__(self):
		output = "({}): {} ".format(self.cost, self.name)
		output += "({}/{})".format(self.power, self.durability)
		return output

""" Inherits from Card. """
class Spell (Card):
	damage = 0
	healing = 0

	def __init__(self, m_dict):
		try:
			self.name = m_dict["name"]
			self.set_id = m_dict["id"]
			self.damage = self.pull_spell_damage(m_dict["text"]) # Can return ValueError
			self.cost = int(m_dict["cost"])		# Can return ValueError
			self.card_text = m_dict["text"]
		except Exception as e:
			print "Exception caught at ", e

		# If the card doesn't inflict damage, self.damage defaults to None.
		# We change that value to 0 to keep type consistency.
		if not type(self.damage) == int:
			self.damage = 0
		# Spell may/not have special mechanics, e.g. Combo, Overload.
		if "mechanics" in m_dict.keys():
			self.mechanics = m_dict["mechanics"]
		# Spell may not be associated with a class.
		if "playerClass" in m_dict.keys():
			self.player_class = m_dict["playerClass"]
		else:
			self.player_class = "NEUTRAL"
		return

	""" Use regex to extract any damage output from the spell. Later
		do the same for healing. Currently doesn't differentiate between
		minion damage and face damage. Also can't figure Shaman spells
		that deal varying amounts of damage. Probably just needs
		a slightly altered regex. 
		Returns an int value."""
	def pull_spell_damage(self, card_text):
		pattern = r"deal (\$\d) damage"
		try:
			match_obj = re.search(pattern, card_text, re.IGNORECASE)
			if match_obj:
				spell_damage = int(match_obj.group(1).replace("$", ""))
				# Wait a second, this if/else might be completely trivial
				# I think I put it here for a reason, but I can't tell why.
				if spell_damage != 0:
					return spell_damage
				else:
					return 0
		except Exception as e:
			print "Exception at ", e
			return 0

	def __str__(self):
		output = "({}) {}: ".format(self.cost, self.name)
		try:
			output += "'{}'".format(self.card_text)
		except:
			print "Exception while extracting card {}'s text. Possibly because it is vanilla and has no card text.".format(self.name)
			pass
		return output






