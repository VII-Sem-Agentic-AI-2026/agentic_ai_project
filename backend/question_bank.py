"""Original practice questions with deterministic answers and explanations."""
# (topic, question, options, correct index, explanation)
APTITUDE=[
 ('Percentages','An item priced at 800 receives a 15% discount. What is the selling price?',['660','680','700','720'],1,'15% of 800 is 120; 800 - 120 = 680.'),
 ('Ratios','Two quantities are in the ratio 3:5 and sum to 64. What is the smaller quantity?',['24','32','40','16'],0,'There are 8 parts. Each is 8, so the smaller quantity is 3 x 8 = 24.'),
 ('Time and work','A completes a task in 12 days and B in 6 days. Working together at constant rates, how long do they take?',['3 days','4 days','6 days','9 days'],1,'Combined rate is 1/12 + 1/6 = 1/4 task per day.'),
 ('Probability','A fair six-sided die is rolled once. What is the probability of an even number?',['1/6','1/3','1/2','2/3'],2,'Three outcomes (2, 4, 6) out of six are even.'),
 ('Averages','The average of 10, 14, 18 and x is 16. What is x?',['18','20','22','24'],2,'The total must be 64. The known values sum to 42, leaving 22.'),
 ('Logical reasoning','All testers are engineers. Some engineers are writers. Which conclusion must follow?',['All testers are writers','Some writers are testers','All testers are engineers','No testers are writers'],2,'Only the original universal statement is guaranteed; the groups of testers and writers may not overlap.'),
 ('Number patterns','What comes next: 3, 7, 15, 31, ...?',['47','60','62','63'],3,'Each term is twice the previous term plus 1.'),
 ('Speed and distance','A vehicle covers 150 km in 2.5 hours. What is its average speed?',['50 km/h','60 km/h','65 km/h','75 km/h'],1,'Average speed is distance/time = 150/2.5 = 60 km/h.'),
 ('Simple interest','What is the simple interest on 2000 at 5% per year for 3 years?',['100','200','300','315'],2,'Simple interest = principal x rate x time = 2000 x 0.05 x 3.'),
 ('Verbal reasoning','Choose the clearest sentence.',['Each of the students have a plan.','Each of the students has a plan.','Each of students has plan.','Each students have a plan.'],1,'Each is singular and takes has; the noun phrase needs the appropriate articles.'),
 ('Combinations','How many different pairs can be chosen from 5 people?',['5','10','15','20'],1,'5 choose 2 = 5 x 4 / 2 = 10.'),
 ('Data interpretation','Sales rise from 120 units to 150 units. What is the percentage increase?',['20%','25%','30%','80%'],1,'Increase is 30; 30/120 x 100 = 25%.')]
TECHNICAL=[
 ('Algorithms','What is the worst-case time complexity of binary search on a sorted array of n elements?',['O(1)','O(log n)','O(n)','O(n log n)'],1,'Binary search halves the remaining search interval each step.'),
 ('Data Structures','Which data structure naturally supports first-in, first-out processing?',['Stack','Queue','Binary search tree','Set'],1,'A queue removes items in their insertion order.'),
 ('SQL','Which clause filters grouped results after GROUP BY?',['WHERE','ORDER BY','HAVING','LIMIT'],2,'HAVING filters groups; WHERE filters rows before grouping.'),
 ('Databases','What does atomicity mean in a database transaction?',['Every query is fast','All transaction operations succeed together or are rolled back','Data is stored once','Tables cannot be joined'],1,'Atomicity gives an all-or-nothing transaction outcome.'),
 ('Python','Which Python collection is mutable?',['tuple','str','list','frozenset'],2,'Lists can have elements added, removed or replaced.'),
 ('REST','Which HTTP method is intended to retrieve a resource without changing server state?',['POST','PATCH','GET','DELETE'],2,'GET has read-only semantics; implementations should not use it for state changes.'),
 ('Git','What is the purpose of a Git commit?',['Upload files to a server automatically','Record a snapshot of staged changes in repository history','Delete untracked files','Install dependencies'],1,'A commit records staged content and metadata locally; pushing is separate.'),
 ('Testing','What is a unit test primarily intended to check?',['A small isolated component or behaviour','Only the visual appearance','The entire internet connection','Whether all users like the product'],0,'Unit tests focus on small components with controlled dependencies.'),
 ('JavaScript','What does await do inside an async function?',['Blocks every browser thread','Pauses that async function until the awaited promise settles','Creates a new operating-system process','Always converts a value to a string'],1,'Await suspends that async function; it does not synchronously block the entire event loop.'),
 ('React','Why should list items have stable keys in React?',['To encrypt component data','To help React identify items across updates','To make CSS mandatory','To send keys to the server'],1,'Stable keys preserve identity when items are inserted, removed or reordered.'),
 ('CSS','Which CSS layout system is designed for one-dimensional row or column layout?',['Flexbox','SQL','HTTP','JSON'],0,'Flexbox arranges items along a primary axis, with optional wrapping.'),
 ('Statistics','Which measure is generally less sensitive to extreme outliers?',['Arithmetic mean','Median','Maximum','Range'],1,'The median depends on ordered position rather than the magnitude of extreme observations.'),
 ('Security','Where should a private Gemini API key be stored for a web application?',['In public frontend JavaScript','In a public GitHub README','In backend secret configuration','In the page title'],2,'A private API key belongs in server-side secret configuration, outside public assets.'),
 ('Networks','What is the primary purpose of DNS?',['Resolve domain names to records such as IP addresses','Compress images','Execute Python','Replace all authentication'],0,'DNS maps names to records needed to locate services.'),
 ('Algorithms','Which traversal uses a queue to explore a graph level by level?',['Depth-first search','Breadth-first search','Binary search','Insertion sort'],1,'Breadth-first search uses a FIFO frontier to visit successive levels.'),
 ('SQL','Which SQL expression counts rows, including rows with NULL values in other columns?',['COUNT(*)','COUNT(nullable_column)','SUM(*)','TOTAL(NULL)'],0,'COUNT(*) counts rows. COUNT(column) counts only non-null values in that column.')]

def questions(kind):
 rows=APTITUDE if kind=='aptitude' else TECHNICAL
 return [dict(id=f'{kind}-{i+1}',topic=t,prompt=p,options=o,answer=a,explanation=e) for i,(t,p,o,a,e) in enumerate(rows)]
