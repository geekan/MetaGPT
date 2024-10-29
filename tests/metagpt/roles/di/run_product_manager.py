import asyncio
import sys

from metagpt.logs import logger
from metagpt.roles import ProductManager

CASE0_WRITE_2048 = """Write a PRD for a cli 2048 game"""
CASE1_GREEDY_SNAKE = "设计一个贪吃蛇游戏"
CASE2_SMART_HOME = "搜索并分析米家、华为智能家居和海尔智家在智能家居市场中的功能、用户需求和市场定位"
CASE3_BEST_SELLING_REFRIGERATOR = "调研当前市场上最畅销的智能冰箱的五个关键特性"
OLD_PRD = """
Language
en_us

Programming Language
N/A

Original Requirements
Write a PRD based on the current music streaming service.

Project Name
music_streaming_service

Product Goals
Enhance user experience with seamless music streaming
Improve accessibility and responsiveness across devices
Expand music library and personalized recommendations
User Stories
As a user, I want to easily search and find my favorite songs and artists.
As a user, I want to create and manage my own playlists.
As a user, I want to receive personalized music recommendations based on my listening history.
As a user, I want to stream music without interruptions or buffering.
As a user, I want to access the service on both desktop and mobile devices.
Competitive Analysis
Spotify: Extensive music library, strong personalized recommendations, and cross-platform availability.
Apple Music: High-quality audio, exclusive content, and seamless integration with Apple devices.
Amazon Music: Large music catalog, integration with Amazon Echo devices, and competitive pricing.
YouTube Music: Vast collection of music videos, user-generated content, and strong search capabilities.
Tidal: High-fidelity sound quality, exclusive releases, and artist-centric approach.
Competitive Quadrant Chart
quadrantChart title "Feature Richness vs. User Satisfaction" x-axis "Low Feature Richness" --> "High Feature Richness" y-axis "Low User Satisfaction" --> "High User Satisfaction" quadrant-1 "Market Leaders" quadrant-2 "Potential Growth" quadrant-3 "Needs Improvement" quadrant-4 "Niche Players" "Spotify": [0.9, 0.85] "Apple Music": [0.85, 0.8] "Amazon Music": [0.75, 0.7] "YouTube Music": [0.8, 0.75] "Tidal": [0.7, 0.65] "Our Target Product": [0.8, 0.8]

Requirement Analysis
The current music streaming service needs to focus on enhancing user experience by providing seamless streaming, improving accessibility, and expanding the music library. Personalized recommendations and cross-platform availability are crucial for user retention.

Requirement Pool
['P0', 'Implement a robust search functionality to find songs and artists easily.']
['P0', 'Develop a feature for users to create and manage playlists.']
['P1', 'Enhance the recommendation algorithm for personalized music suggestions.']
['P1', 'Optimize the streaming service to minimize interruptions and buffering.']
['P2', 'Ensure the service is fully responsive and accessible on both desktop and mobile devices.']
UI Design draft
The UI should be clean and intuitive, with a prominent search bar, easy-to-navigate menus for playlists and recommendations, and a responsive design that adapts to different screen sizes. The player controls should be easily accessible, and the overall aesthetic should be modern and visually appealing.

Anything UNCLEAR
Currently, all aspects of the project are clear.
"""
CASE4_MUSIC_STREAMING_MEDIA = f"""We have received feedback from users regarding the current music streaming service, stating that they need better personalized recommendations. Please readjust the content of PRD {OLD_PRD} based on these feedback."""
CASE5_SMART_BIG_SCREEN = """分析2024年上半年中国家庭智能大屏行业的发展情况并输出市场分析报告"""
CASE6_ELECTRONIC_CIGARETTE = """我想要生产一个电子烟产品，请帮我完成市场调研分析报告"""


def main():
    cases = [
        # CASE0_WRITE_2048,
        # CASE1_GREEDY_SNAKE,
        # CASE2_SMART_HOME,
        # CASE3_BEST_SELLING_REFRIGERATOR,
        # CASE4_MUSIC_STREAMING_MEDIA,
        CASE5_SMART_BIG_SCREEN,
        # CASE6_ELECTRONIC_CIGARETTE,
    ]
    root_path = "/tmp"
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    for case in cases:
        case += f"\nroot path: '{root_path}'"
        logger.info(f"user requirement:\n{case}")
        try:
            product_manager = ProductManager()
            asyncio.run(product_manager.run(case))
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
