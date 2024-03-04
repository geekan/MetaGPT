import fire
from metagpt.roles.mi.math_expert import MathExpert

# C.prob 容易
p1 = """Roslyn has ten boxes. 
Five of the boxes contain pencils, four of the boxes contain pens, and two of the boxes contain both pens and pencils. 
How many boxes contain neither pens nor pencils?"""

# C.prob 难
p2 = """Three points are chosen randomly and independently on a circle. 
What is the probability that all three pairwise distances between the points are less than the radius of the circle?"""

# C.prob 简单
p3 = """How many positive integers less than or equal to 100 have a prime factor that is greater than 4?"""

# C.prob 难
p4 = """Three points are chosen randomly and independently on a circle. 
What is the probability that all three pairwise distances between the points are less than the radius of the circle?"""

# C.prob 难
p5 = """How many ways are there for 8 people to sit around a circular table if none of Alice, 
Bob, and Eve (three of the 8 people) want to sit next to each other? 
Two seatings are considered the same if one is a rotation of the other."""

select_problem = p1


if __name__ == "__main__":

    async def main(requirement: str = select_problem,):
        role = MathExpert()
        _ = await role.run(requirement)
        print('answer : ', role.answer)
        print('csv_result : ', role.csv_result)


    fire.Fire(main)
