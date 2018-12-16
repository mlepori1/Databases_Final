import spacy

class Parser():

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


    def parse_deps(self, deps):
        for d in deps:
            if d.text == "miles":
                last_deps = [child.text for child in d.children]
                for l in last_deps:
                    if l.isdigit():
                        return int(l)
            else:            
                return self.parse_deps([child for child in d.children])


    def analyze(self):
        
        state_code = []
        longer = -1
        shorter = -1
        dog_allow = 1
        dog_type = "any"
        diff = ""
        diff_preference = 1
        rating = -1

        for state in self.states.keys():
            if state in self.query:
                if state == "virginia" or state == "washington":
                    tokens = self.query.split()
                    idx = tokens.index(state)
                    if tokens[idx-1] == "west":
                        continue
                    if len(tokens) >= idx + 2:
                        if tokens[idx+1] == "dc":
                            continue

                state_code.append(self.states[state])
        

        if " allow " in self.query or " allows ":
            for t in self.ling:

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
                        

        if " longer " in self.query:

            candidates = []

            for t in self.ling:

                if t.text  == "longer":
                    dep = [child for child in t.children]
                    candidates.append(self.parse_deps(dep))

                if t.dep_ == "nummod":
                    dep = [child.text for child in t.children]
                    if "longer" in dep:
                        candidates.append(int(t.text))

                
            longer = candidates[-1]
                    

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


        if " rated " in self.query:
            for t in self.ling:
                if t.dep_ == "nummod" and t.head.text == "stars":
                    rating = float(t.text)
        
        return [state_code, longer, shorter, dog_allow, dog_type, diff, diff_preference, rating]

    
    def generate_sql(self, features):

        base_sql_q = "SELECT Name\nFROM Hike, HikeName, Locations, Ratings, Dogs\n" \
        "WHERE Hike.HikeID = HikeName.HikeID AND Hike.HikeID = Locations.HikeID\nAND " \
        "Hike.HikeID = Ratings.HikeID AND Hike.HikeID = Dogs.HikeID\n"

        if features[0] != []: 

            base_sql_q += "AND (Locations.State LIKE \"" + features[0][0]

            for i in range(1, len(features[0])):
                base_sql_q += "\" OR Locations.State LIKE \"" + features[0][i]

            base_sql_q += "\")\n"


        if features[1] != -1:
            base_sql_q += "AND Hike.Length > " + str(features[1]) + "\n"


        if features[2] != -1:
            base_sql_q += "AND Hike.Length < " + str(features[2]) + "\n"

        if features[3] == -1 and features[4] == "any":
            base_sql_q += "AND Dogs.Dog LIKE \"No Dogs\"\n" 

        if features[3] == 1 and features[4] == "any":
            base_sql_q += "AND Dogs.Dog NOT LIKE \"No Dogs\"\n"
        
        if features[3] == 1 and features[4] != "any":
            base_sql_q += "AND Dogs.Dog LIKE \"" + features[4] + "\"\n"

        if features[3] == -1 and features[4] != "any":
            base_sql_q += "AND Dogs.Dog NOT LIKE \"" + features[4] + "\"\n"

        if features[5] != "":
            if features[6] == 1:
                base_sql_q += "AND Hike.difficulty LIKE \"" + features[5] + "\"\n"
            else:
                base_sql_q += "AND Hike.difficulty NOT LIKE \"" + features[5] + "\"\n"

        if features[7] != -1:
            base_sql_q += "AND Ratings.Average_Rating >= " + str(features[7]) + "\n"

        base_sql_q += ";"

        self.sql = base_sql_q

        return base_sql_q



if __name__ == "__main__":

    parse = Parser("Show me all easy trails that are in California or Montana and do not allow leashed dogs that are rated above 3.5 stars and that are longer than 2 miles and shorter than 5 miles.")

    parse.generate_sql(parse.analyze())

    parse.print_sql()

    