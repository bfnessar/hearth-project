import requests
import json
import os
import pprint
import pymongo
import string
import re
import card as c

""" Notes to self:
		* Don't give any local variables the name 'minion', because that's also the 
			name of the minion module.

"""

class HearthLodge:

	""" Internal variables. """
	#address = "http://api.hearthstonejson.com/v1/latest/"
	file_location = os.getcwd() + "/cards.collectible.json"
	raw_list = []
	cards_dict = {} # Key: cardname; Value: attribute_dict.
	cards_allnames_str = ""

	""" Currently has the location of the data archive hard-coded, but I guess that later it should
		accept a location as an argument. Not really a concern right now. """
	def __init__(self):
		self.load_data_from_file()
		self.raw_data_to_dict()
		self.load_allnames_str()
		return

	""" Loads the data from a hard-coded location (stored internally). Loads the data to self.raw_list, which is
		a list of dictionaries. Next step would be to take that data and convert it to a dictionary with 
		key=card_name. """
	def load_data_from_file(self):
		# Error-checking would go here.

		# Load the file to internal list
		with open(self.file_location, "r") as fp:
			self.raw_list = json.loads(fp.read())
		return

	""" Takes the data from raw_list and converts it to a dictionary, where entries are accessed by card name. 
		I.e., takes the data from self.raw_list and transfers it to self.cards_dict"""
	def raw_data_to_dict(self):
		# Iterates over entries in self.raw_list
		for entry in self.raw_list:
			self.cards_dict[entry["name"]] = entry
		return

	""" Takes all the stored cardnames and appends them to one long string. Will use this for 
		pattern-matching/ regular expression cardname lookups. """
	def load_allnames_str(self):
		for cardname in self.cards_dict.keys():
			self.cards_allnames_str += (cardname + "; ")
		return

	#=======================================================##=======================================================#
	#=======================================================##=======================================================#
	#=======================================================##=======================================================#
	#=======================================================##=======================================================#

	""" Return a list of damaging spells (using regex). Use this in 
		conjunction with contested_by() to see which spells threaten a given minion.
		Could also be useful with minion effects (battlecries, specifically),
		but for now let's focus on spells. """
	def pull_spell_threats(self, guy):
		pattern = r"deal (\$\d) damage" # This is the pattern we are applying
		matches = {} # Dictionary of spell objects that deal damage.
		for card in self.cards_dict.values():
			# Reminder: 'card' is a dictionary
			if card["type"] == "SPELL":
				try:
					s = c.Spell(card)
					if s.damage != 0:
						matches[card["name"]] = s
				except KeyError, e:
					print "Keyerror on ", card["name"]
					continue
		# Now we have a dictionary full of damaging spells. We iterate over the spell objects
		# to see if they can cost-efficiently remove the given minion.
		threats = []
		for card in matches.values():
			if (card.cost <= guy.cost and card.damage >= guy.health):
				threats.append(card)
		# print "PULLING SPELL THREATS...: "
		# for threat in threats:
		# 	print str(threat)
		return threats

	def pull_weapon_threats(self, guy):
		# Create a list of all weapons. If we get some database
		# functionality, this part of the process might become
		# unnecessary. But as it stands, this is what we're doing.
		weapons = []
		for card in self.cards_dict.values():
			if card["type"] == "WEAPON":
				try:
					w = c.Weapon(card)
					weapons.append(w)
				except Exception as e:
					print "Exception on ", card["name"]
					continue
		# 'threats' refers to weapons that can kill your guy if played on curve.
		threats = []
		for w in weapons:
			if (w.cost <= guy.cost and w.power >= guy.health):
				threats.append(w)
		return threats

	""" Looks for cards in the database with a similar name as the sought target.
		Returns a list containing all matches. Uses regular expressions. """
	def partial_name_lookup(self, partial_name):
		# Take the given, partial name and turn it into a regex pattern.
		regex_pattern = r"(.*)" + re.escape(partial_name) + r"(.*)"
		# Stores the list of matches
		matches = []
		# Search the list of card names (stored in dict.keys())
		for cardname in self.cards_dict.keys():
			# If the pattern matches a string, store the matched string in 
			# the following variable, which is of type 'match object'. If no match,
			# then the variable is None or False or some such thing.
			match_obj = re.search(regex_pattern, cardname, re.IGNORECASE)
			if match_obj:
				matches.append(match_obj.group())
		return matches

	""" Given a list of minion objects: 
			Create a dictionary that maps each class to its subset of minions in the list;
			Sort each list by cost. 
		Return the new dictionary.
	"""
	def categorize_list(self, m_list):
		# This is the dictionary that gets filled out.
		arranged_dict = {"NEUTRAL": [], "DRUID": [], "HUNTER": [], "MAGE": [], \
		"PALADIN": [], "PRIEST": [], "ROGUE": [], "SHAMAN": [], \
		"WARLOCK": [], "WARRIOR": []}

		# Add each minion to its corresponding list in the dictionary
		for m in m_list:
			p_class = m.player_class
			arranged_dict[p_class].append(m)
		# Sort each list by cost.
		for sublist in arranged_dict.values():
			# This syntax looks like a bunch of gibberish but it works
			# Does an in-place sort on each class's threats list (sorted by cost)
			sublist.sort(key=lambda x: x.cost)
		return arranged_dict

	""" Pretty-prints whatever item you pass it. """
	def pp_item(self, printable):
		pp = pprint.PrettyPrinter(indent=2)
		pp.pprint(printable)
		return

	""" Returns a dictionary representation of targeted card. """
	def query_card(self, card_name):
		if card_name in self.cards_dict.keys():
			return self.cards_dict[card_name]
		else:
			return False

	""" Given a minion object (assumed to be legitimate), 
		returns a list of minions that contest that minion.
		"Contests" (v.) is defined as: minion m1 contests minion m2 if
		(m2.attack >= m1.health) && (m2.cost <= m1.cost). 
		Returns a list of candidates for minions m2. """
	def contested_by(self, m1):
		# First get a list of minions that fit the cost requirement, i.e. minions
		# that could already be on the board given both players are playing on curve.
		castable_minions = [] # List of minion objects
		for m in self.cards_dict.values():
			if (m["type"] == "MINION" and m["cost"] <= m1.cost):
				m2 = c.Minion()
				m2.load_from_dict(m)
				castable_minions.append(m2)

		# Now, we iterate over the list of on-curve minions and see which ones
		# counter the target minion
		castable_threats = []
		for m2 in castable_minions: # m2 is a minion object
			if m2.attack >= m1.health: # Determine that m2 can OHKO m1
				castable_threats.append(m2)

		# Return the list of threats that can be summoned that contest this minion
		return castable_threats


	def user_loop(self):
		print "Shell open. Enter 'h' or 'help' for a list of commands."
		while True:
			prompt = raw_input("HEARTH >>> ")

			if prompt == "q":
				break
			if prompt == "p":
				self.pp_item(self.cards_dict)
				continue
			if prompt == "names":
				print self.cards_allnames_str
				continue
			if prompt in ["h", "help"]:
				help_prompt = "Your available commands are: \n"
				help_prompt += "  'names' prints a list of all card names\n"
				help_prompt += "  'p' prints the entire dictionary, unfiltered.\n"
				help_prompt += "  'lookup <cardname>' prints data for the requested card.\n"
				help_prompt += "  'regex <substring>' prints a list of cards whose names contain <substring>.\n"
				help_prompt += "  'threats <minion>' prints a list of minions that threaten the targeted minion.\n"
				print help_prompt
				continue

			# "d" for "debugging". Sometimes I put little tests and stuff in here.
			if prompt == "d":
				guy = c.Minion(self.cards_dict["Knife Juggler"])
				weapons = self.pull_weapon_threats(guy)
				for result in weapons:
					print str(result)
				continue


			# In case of multiple-word prompts, e.g. card lookup.
			if len(prompt.split()) > 1:
				# Split the prompt into <command>, <target>
				command = prompt.split()[0] # Contains <command>
				target = prompt.split(' ', 1)[1] # Contains <target>, arbitrary number of words, tokens separated by whitespace.

				# User wants to look up <target> card.
				if command == "lookup":
					response = self.query_card(target)
					self.pp_item(response)
					continue

				# Looks up cards using 're' module for regular expressions. Gets a list of
				# matches, then prints out the list iteratively.
				if command == "regex":
					matches = self.partial_name_lookup(target)
					if len(matches) > 0:
						print "Found a match for ", target, "!"
						for entry in matches:
							print entry
					else:
						print "Found no matches for ", target
					continue

				# Looks up minions with a specific attribute
				# Format is: 'minions atk=4', 'minions cost=3', etc.
				# This functionality is still kind of buggy. Probably should port to its own
				# function, then fix it.
				if command == "minions":
					targets = target.split()

					params = {} # Key/Values, e.g. 'params["atk"] = 3'
					for stat in targets:
						stat = stat.split("=")
						try:
							if (stat[0] in ["attack", "health", "cost"] and int(stat[1])):
								params[stat[0]] = int(stat[1]) # Assign the stat value to its name
							else:
								print "{} doesn't compute".format(stat)
								print "Bailing out"
								return

						except ValueError, e:
							print "ValueError on {}.\nProbably because {} is not an integer.".format(e, stat[1])
							break
					matches = []
					for guy in self.cards_dict.values():
						if guy["type"] == "MINION":
							is_a_match = True
							for param in params.keys():
								# print "{} {}, equals?, {} {}".format(type(guy[param]), guy[param], type(params[param]), params[param])
								if int(guy[param]) != params[param]:
									is_a_match = False
							if is_a_match:
								m = c.Minion(guy)
								matches.append(m)
					for guy in matches:
						print str(guy)
					continue

				# Looks up threats to a given card. Returns a list of counters to target minion.
				if command == "threats":
					# Create a minion object and load it up
					m = c.Minion(self.cards_dict[target])
					# Make a list of minions that threaten your target
					minion_threats = self.contested_by(m)
					# Do the same for spells
					spell_threats = self.pull_spell_threats(m)
					# Lastly, do this for weapons.
					weapon_threats = self.pull_weapon_threats(m)
					# Combine the above lists
					all_threats = minion_threats + spell_threats + weapon_threats

					# Now we format the information and print it in an organized way.
					sorted_threats = self.categorize_list(all_threats)
					for champ in sorted_threats.keys():
						# If a champion doesn't have a response, don't bother.
						if len(sorted_threats[champ]) == 0:
							print champ, " has no class-specific responses. Check NEUTRAL class for answers."
						else:
							print champ
							print "  (minions): "
							for card in sorted_threats[champ]:
								if isinstance(card, c.Minion):
									print "    ", str(card)
							print "  (spells): "
							for card in sorted_threats[champ]:
								if isinstance(card, c.Spell):
									print "    ", str(card)
							print "  (weapons): "
							for card in sorted_threats[champ]:
								if isinstance(card, c.Weapon):
									print "    ", str(card)

					continue

		return


if __name__ == "__main__":
	hl = HearthLodge()
	hl.user_loop()