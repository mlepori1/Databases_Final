import spacy

'''
Michael Lepori/Parth Singh
315/415 Final Project
Natural Language Parser

This class takes natural language input and converts it into
SQL queries

REQUIRES SPACY AND ITS "EN" MODEL
https://spacy.io/usage/models
'''

class Parser():

    # For parsing statecodes from language
    states = {
        "alabama":  "AL",
        "alaska" : "AK",
        "arizona" : "AZ",
        "arkansas" : "AR",
        "california" : "CA",
        "colorado" : "CO",
        "connecticut" : "CT",
        "delaware" : "DE",
        "florida" : "FL",
        "georgia" : "GA",
        "hawaii" : "HI",
        "idaho" : "ID",
        "illinois" : "IL",
        "indiana" : "IN",
        "iowa" : "IA",
        "kansas" : "KS",
        "kentucky" : "KY",
        "louisiana" : "LA",
        "maine" : "ME",
        "maryland" : "MD",
        "massachusetts" : "MA",
        "michigan" : "MI",
        "minnesota" : "MN",
        "mississippi" : "MS",
        "missouri" : "MO",
        "montana" : "MT",
        "nebraska" : "NE",
        "nevada" : "NV",
        "new hampshire" : "NH",
        "new jersey" : "NJ",
        "new mexico" : "NM",
        "new york" : "NY",
        "north carolina" : "NC",
        "north dakota" : "ND",
        "ohio" : "OH",
        "oklahoma" : "OK",
        "oregon" : "OR",
        "pennsylvania" : "PA",
        "rhode island" : "RI",
        "south carolina" : "SC",
        "south dakota" : "SD",
        "tennessee" : "TN",
        "texas" : "TX",
        "utah" : "UT",
        "vermont" : "VT",
        "virginia" : "VA",
        "washington" : "WA",
        "wisconsin" : "WI",
        "west virginia" : "WV",
        "wyoming" : "WY",
        "washington dc" : "DC"
    }


    # Class variables containint natural language query, linguistic parse, and sql query
    query = ""
    ling = ""
    sql = ""


    def __init__(self, q):

        nlp = spacy.load('en')
        self.query = q.lower()
        self.ling = nlp(q)


    def new_query(self, new_q):
        self.query = new_q.lower()
        self.ling = nlp(new_q)


    def current_query(self):
        return self.query


    def print_sql(self):
        print(self.sql)
        return


    def return_sql(self): return self.sql


    # Helper function to parse through dependency tree and find
    # the number of miles in a shorter/longer than query
    def parse_deps(self, deps):
        for d in deps:
            if d.text == "miles":
                last_deps = [child.text for child in d.children]
                for l in last_deps:
                    if l.isdigit():
                        return int(l)
            else:            
                return self.parse_deps([child for child in d.children])


    # This function extracts the supported info from natural language strings
    # and returns a list of features to be converted into SQL
    def analyze(self):
        
        # Initializes all features to default values
        state_code = []     # List of desired states
        longer = -1     # Trail should be longer than this
        shorter = -1    # Trail should be shorter than this 
        dog_allow = 0   # 1 for allows, -1 for doesn't allow
        dog_type = "any"    # leashed/off-leashed/any
        diff = ""   # difficulty
        diff_preference = 1     # 1 for should be this difficult, -1 for shouldn't be
        rating = -1     # Trail should have more than this number of stars

        # Parses through query to find which states are desired by user
        for state in self.states.keys():
            if state in self.query:
                if state == "virginia" or state == "washington":    # These state names are also substrings of
                    tokens = self.query.split()                     # other state names
                    idx = tokens.index(state)
                    if tokens[idx-1] == "west":
                        continue
                    if len(tokens) >= idx + 2:
                        if tokens[idx+1] == "dc":
                            continue

                state_code.append(self.states[state])
        

        # Extracts dog information
        if " allow " in self.query or " allows " in self.query:
            dog_allow = 1
            for t in self.ling:
                # Parses through dependency trees for this information
                if t.text == "allow":
                    dep = [child.text for child in t.children]
                    if "dog" in dep or "dogs" in dep:
                        if "not" in dep:
                            dog_allow = -1

                if t.text == "dogs" or t.text == "dog":
                    dep = [child.text for child in t.children]
                    if "leashed" in dep:
                        dog_type = "Leashed"
                    if "off-leashed" in dep:
                        dog_type = "Off-leash"
                        

        # Extracts longer than information
        if " longer " in self.query:

            candidates = []

            # Depending on the syntax of the query, this information will
            # be gathered in one of two ways
            for t in self.ling:

                # Sometimes appends NONE, else is correct
                if t.text  == "longer":
                    dep = [child for child in t.children]
                    candidates.append(self.parse_deps(dep))

                # Is correct when the above returns NONE, else doesn't append
                if t.dep_ == "nummod":
                    dep = [child.text for child in t.children]
                    if "longer" in dep:
                        candidates.append(int(t.text))

            # Last element is thus always correct
            longer = candidates[-1]
                    

        # Extracts shorter than information in a similar way
        if " shorter " in self.query:

            candidates = []

            for t in self.ling:

                if t.text == "shorter":
                    dep = [child for child in t.children]
                    candidates.append(self.parse_deps(dep))

                if t.dep_ == "nummod":
                    dep = [child.text for child in t.children]
                    if "shorter" in dep:
                        candidates.append(int(t.text))

            shorter = candidates[-1]

                    
        # Extracts difficulty information, diff_preference information could be found in
        # 2 places, checks them both
        if " easy " in self.query or " intermediate " in self.query or " difficult " in self.query:
            for t in self.ling:
                if t.text == "easy":
                    dep = [child.text for child in t.children]
                    diff = "easy"
                    if "not" in dep:
                        diff_preference = -1
                if t.text == "intermediate":
                    dep = [child.text for child in t.children]
                    diff = "intermediate"
                    if "not" in dep:
                        diff_preference = -1             
                if t.text == "difficult":
                    dep = [child.text for child in t.children]
                    diff = "difficult"
                    if "not" in dep:
                        diff_preference = -1

                dep = [child.text for child in t.children]
                if ("easy" in dep or "intermediate" in dep or "difficult" in dep) and "not" in dep:
                    diff_preference = -1


        # Extracts rating information
        if " rated " in self.query:
            for t in self.ling:
                if t.dep_ == "nummod" and t.head.text == "stars":
                    rating = float(t.text)
        
        return [state_code, longer, shorter, dog_allow, dog_type, diff, diff_preference, rating]

    
    # Takes the list of features generated by analyze and generates SQL code from it
    def generate_sql(self, features):

        # Basic SQL template
        base_sql_q = "SELECT Name\nFROM Hike, HikeName, Locations, Ratings, Dogs\n" \
        "WHERE Hike.HikeID = HikeName.HikeID AND Hike.HikeID = Locations.HikeID\nAND " \
        "Hike.HikeID = Ratings.HikeID AND Hike.HikeID = Dogs.HikeID\n"

        # If there are state preferences, add those to SQL
        if features[0] != []: 

            base_sql_q += "AND (Locations.State LIKE \"" + features[0][0]

            for i in range(1, len(features[0])):
                base_sql_q += "\" OR Locations.State LIKE \"" + features[0][i]

            base_sql_q += "\")\n"

        # Longer than preferences
        if features[1] != -1:
            base_sql_q += "AND Hike.Length > " + str(features[1]) + "\n"

        # Shorter than preferences
        if features[2] != -1:
            base_sql_q += "AND Hike.Length < " + str(features[2]) + "\n"

        # Handles all combinations of dog_type and dog_allow preferences
        if features[3] == -1 and features[4] == "any":
            base_sql_q += "AND Dogs.Dog LIKE \"No Dogs\"\n" 

        if features[3] == 1 and features[4] == "any":
            base_sql_q += "AND Dogs.Dog NOT LIKE \"No Dogs\"\n"
        
        if features[3] == 1 and features[4] != "any":
            base_sql_q += "AND Dogs.Dog LIKE \"" + features[4] + "\"\n"

        if features[3] == -1 and features[4] != "any":
            base_sql_q += "AND Dogs.Dog NOT LIKE \"" + features[4] + "\"\n"

        # Handles all combinations of difficulty preferences
        if features[5] != "":
            if features[6] == 1:
                base_sql_q += "AND Hike.difficulty LIKE \"" + features[5] + "\"\n"
            else:
                base_sql_q += "AND Hike.difficulty NOT LIKE \"" + features[5] + "\"\n"

        # Handles rating preferences
        if features[7] != -1:
            base_sql_q += "AND Ratings.Average_Rating >= " + str(features[7]) + "\n"

        base_sql_q += ";"

        self.sql = base_sql_q

        return base_sql_q



if __name__ == "__main__":

    parse = Parser( "Show me all easy trails that are in California or Montana and do not allow leashed dogs that are rated above 3.5 stars and that are longer than 2 miles and shorter than 5 miles.")

    parse.generate_sql(parse.analyze())

    parse.print_sql()

    