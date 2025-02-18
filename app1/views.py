import requests
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile
from bs4 import BeautifulSoup

# Fetch LeetCode stats
def get_leetcode_stats(username):
    url = "https://leetcode.com/graphql/"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }
    query = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            username
            profile {
                reputation
                ranking
            }
            submitStatsGlobal {
                acSubmissionNum {
                    difficulty
                    count
                }
            }
            languageProblemCount {
                languageName
                problemsSolved
            }
            badges {
                displayName
            }
            userCalendar {
                activeYears
                streak
                totalActiveDays
            }
        }
        userContestRanking(username: $username) {
            attendedContestsCount
            rating
            globalRanking
            totalParticipants
            topPercentage
            badge {
                name
            }
        }
        activeDailyCodingChallengeQuestion {
            link
            question {
                title
                titleSlug
            }
        }
    }
    """
    variables = {"username": username}
    data = {"query": query, "variables": variables}

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        json_data = response.json()
        if "errors" in json_data:
            print(f"Error in LeetCode API response: {json_data['errors']}")
            return None

        user_data = json_data.get("data", {}).get("matchedUser", None)
        daily_challenge = json_data.get("data", {}).get("activeDailyCodingChallengeQuestion", None)
        contest_data = json_data.get("data", {}).get("userContestRanking", None)

        if not user_data:
            return None

        # General Profile Stats
        ranking = user_data["profile"].get("ranking", "N/A")
        submissions = user_data["submitStatsGlobal"]["acSubmissionNum"]
        easy = next((x["count"] for x in submissions if x["difficulty"] == "Easy"), 0)
        medium = next((x["count"] for x in submissions if x["difficulty"] == "Medium"), 0)
        hard = next((x["count"] for x in submissions if x["difficulty"] == "Hard"), 0)
        total_solved = easy + medium + hard

        # Language-Specific Stats
        language_data = user_data.get("languageProblemCount", [])
        cpp_solved = next((d["problemsSolved"] for d in language_data if d["languageName"] == "C++"), 0)
        python_solved = next((d["problemsSolved"] for d in language_data if d["languageName"] == "Python3"), 0)

        # Contest Stats
        contests_attended = contest_data.get("attendedContestsCount", "N/A") if contest_data else "N/A"
        contest_rating = contest_data.get("rating", "N/A") if contest_data else "N/A"
        global_rank = contest_data.get("globalRanking", "N/A") if contest_data else "N/A"
        total_participants = contest_data.get("totalParticipants", "N/A") if contest_data else "N/A"
        top_percentage = contest_data.get("topPercentage", "N/A") if contest_data else "N/A"

        # Badge Display Names
        badges = user_data.get("badges", [])
        badge_display_names = [badge.get("displayName", "N/A") for badge in badges]
        
        # Calendar Stats
        user_calendar = user_data.get("userCalendar", {})
        total_active_days = user_calendar.get("totalActiveDays", "N/A")
        streak = user_calendar.get("streak", "N/A")

        # Daily Challenge Question
        daily_challenge_title = daily_challenge["question"]["title"] if daily_challenge else "No active challenge"
        daily_challenge_link = f"https://leetcode.com{daily_challenge['link']}" if daily_challenge else "#"

        return {
            "username": username,
            "ranking": ranking,
            "total_solved": total_solved,
            "easy": easy,
            "medium": medium,
            "hard": hard,
            "cpp_solved": cpp_solved,
            "python_solved": python_solved,
            "contests_attended": contests_attended,
            "contest_rating": contest_rating,
            "global_rank": global_rank,
            "total_participants": total_participants,
            "top_percentage": top_percentage,
            "badges": badge_display_names,
            "total_active_days": total_active_days,
            "streak": streak,
            "daily_challenge_title": daily_challenge_title,
            "daily_challenge_link": daily_challenge_link,
        }
    except Exception as e:
        print(f"Error fetching LeetCode data: {e}")
        return None


# Fetch upcoming LeetCode contests
def get_upcoming_contests():
    url = "https://leetcode.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com/contest/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    query = {
        "query": """
        query {
            topTwoContests {
                title
                titleSlug
                startTime
                duration
            }
        }
        """
    }

    try:
        response = requests.post(url, json=query, headers=headers)
        response.raise_for_status()
        data = response.json()

        contests = data["data"]["topTwoContests"]
        upcoming_contests = []
        if contests:
            for contest in contests:
                title = contest["title"]
                slug = contest["titleSlug"]
                start_time = datetime.utcfromtimestamp(contest["startTime"]).strftime('%Y-%m-%d %H:%M:%S')
                duration = contest["duration"] // 60  # Convert duration to minutes

                upcoming_contests.append({
                    "title": title,
                    "url": f"https://leetcode.com/contest/{slug}/",
                    "start_time": start_time,
                    "duration": duration
                })
        return upcoming_contests
    except requests.exceptions.RequestException as e:
        print(f"Error fetching contests: {e}")
        return []


def get_codechef_stats(username):
    url = f"https://www.codechef.com/users/{username}"

    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch page. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    try:
        rating = soup.find('div', class_='rating-number').text.strip()
        print(f"Rating: {rating}")
        
        global_rank_tag = soup.find('a', href='/ratings/all')
        global_rank = global_rank_tag.text.strip() if global_rank_tag else "Inactive"
        print(f"Global Rank: {global_rank}")
        
        country_rank_tag = soup.find('a', href='/ratings/all?filterBy=Country%3DIndia')
        country_rank = country_rank_tag.text.strip() if country_rank_tag else "Inactive"
        print(f"Country Rank: {country_rank}")
        
        stars = soup.find('span', class_='rating').text.split()[0].strip()
        print(f"Stars: {stars}")
        
        # Get the total problems solved
        problems_solved_tag = soup.find('h3', string=lambda s: s and 'Total Problems Solved' in s)
        problems_solved = problems_solved_tag.text.split(':')[-1].strip() if problems_solved_tag else "N/A"
        
        badges_section = soup.find_all('div', class_='badge')
        badges = []
        if badges_section:
            for badge in badges_section:
                title = badge.find('p', class_='badge__title').text.strip()
                description = badge.find('p', class_='badge__description').text.strip()
                badges.append({'title': title, 'description': description})
        print(f"Badges: {badges}")
        
        contests_participated_tag = soup.find('div', class_='contest-participated-count')
        contests_participated = contests_participated_tag.find('b').text.strip() if contests_participated_tag else "N/A"
        
        return {
            'rating': rating,
            'global_rank': global_rank,
            'country_rank': country_rank,
            'stars': stars,
            'problems_solved': problems_solved,
            'badges': badges,
            'contests_participated': contests_participated,
        }
    except AttributeError as e:
        print(f"Error parsing CodeChef data: {e}")
        return None


def get_codeforces_rating(username):
    url = f"https://codeforces.com/api/user.info?handles={username}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "result" in data and data["result"]:
                user_info = data["result"][0]
                rating = user_info.get("rating", "Unrated")
                max_rating = user_info.get("maxRating", "Unrated")
                rank = user_info.get("rank", "Unknown")
                return {
                    "username": username,
                    "rating": rating,
                    "max_rating": max_rating,
                    "rank": rank
                }
            else:
                print(f"User {username} not found or no rating available.\n")
                return None
        else:
            print(f"Failed to fetch user data. Status code: {response.status_code}\n")
            return None
    except Exception as e:
        print(f"An error occurred while fetching user rating: {e}\n")
        return None

# Function to get upcoming Codeforces contests
def get_upcoming_codeforces_contests():
    url = "https://codeforces.com/api/contest.list"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] == "OK":
            contests = data["result"]
            upcoming_contests = []
            
            # Filter contests that haven't started yet
            for contest in contests:
                if contest["phase"] == "BEFORE":
                    start_time = datetime.utcfromtimestamp(contest["startTimeSeconds"])
                    duration = timedelta(seconds=contest["durationSeconds"])
                    upcoming_contests.append({
                        "name": contest["name"],
                        "start_time": start_time,
                        "duration": duration
                    })
            
            return upcoming_contests
        else:
            print("Failed to fetch contest data. API returned an error.\n")
            return []
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching contests: {e}\n")
        return []    



def fetch_user_profile(username):
    url = f"https://www.geeksforgeeks.org/user/{username}/"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract rank
        rank = soup.find('span', class_='educationDetails_head_left_userRankContainer--text__wt81s')
        rank = rank.text.strip() if rank else "N/A"

        # Extract language used
        language = soup.find('div', class_='educationDetails_head_right--text__lLOHI')
        language = language.text.strip() if language else "N/A"

        # Extract scores (coding score, problems solved, contest rating)
        scores = soup.find_all('div', class_='scoreCard_head_left--score__oSi_x')
        coding_score = scores[0].text.strip() if len(scores) > 0 else "N/A"
        problems_solved = scores[1].text.strip() if len(scores) > 1 else "N/A"
        contest_rating = scores[2].text.strip() if len(scores) > 2 else "N/A"

        # Extract difficulty levels
        difficulty_divs = soup.find_all('div', class_='problemNavbar_head_nav__a4K6P')
        difficulties = []
        for div in difficulty_divs:
            text_div = div.find('div', class_='problemNavbar_head_nav--text__UaGCx')
            if text_div:
                full_text = text_div.text.strip()
                if '(' in full_text and ')' in full_text:
                    difficulty, count = full_text.rsplit('(', 1)
                    difficulty = difficulty.strip()
                    count = count.strip(')').strip()
                    difficulties.append({"difficulty": difficulty, "count": count})

        return {
            "rank": rank,
            "language": language,
            "coding_score": coding_score,
            "problems_solved": problems_solved,
            "contest_rating": contest_rating,
            "difficulties": difficulties,
            "problem_of_the_day": "https://www.geeksforgeeks.org/problem-of-the-day"
        }

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Function to fetch weekly contest details
def fetch_weekly_contests():
    url = "https://www.geeksforgeeks.org/events/rec/gfg-weekly-coding-contest"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the section for upcoming events
        upcoming_events = soup.find_all("div", class_="events_upcomingEvent__eOm_s")
        contests = []

        # Extract information about each contest
        for event in upcoming_events:
            try:
                # Extract date
                date = event.find("p", class_="events_upcomingEventDescDate__lJC3I").text.strip()
                # Extract contest name
                contest_name = event.find("p", class_="events_upcomingEventDescTxt__xgvgK").text.strip()
                # Extract questions, marks, and duration
                stats = event.find_all("span", class_="sofia-pro")
                num_questions = stats[0].text.strip() if stats else "N/A"
                marks = stats[1].text.strip() if len(stats) > 1 else "N/A"
                duration = stats[2].text.strip() if len(stats) > 2 else "N/A"

                contests.append({
                    "contest_name": contest_name,
                    "date": date,
                    "num_questions": num_questions,
                    "marks": marks,
                    "duration": duration
                })
            except Exception as e:
                print(f"Error parsing event: {e}")

        return contests

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


    
# Register user
def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        leetcode_username = request.POST.get('leetcode_username', '').strip()
        codechef_username = request.POST.get('codechef_username', '').strip()
        codeforces_username = request.POST.get('codeforces_username', '').strip()
        gfg_username = request.POST.get('gfg_username', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
            else:
                user = User.objects.create_user(username=username, first_name=name, email=email, password=password)
                UserProfile.objects.create(
                    user=user,
                    leetcode_username=leetcode_username,
                    codechef_username=codechef_username,
                    codeforces_username=codeforces_username,
                    gfg_username=gfg_username
                )
                messages.success(request, 'Registration successful! Please log in.')
                return redirect('login')
        else:
            messages.error(request, 'Passwords do not match.')

    return render(request, 'register.html')

# Login user
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


# Logout user
def logout_view(request):
    logout(request)
    return redirect('login')


# Home page
@login_required
def home(request):
    return render(request, 'home.html')

# LeetCode Page
@login_required
def leetcode_view(request):
    profile = None
    leetcode_data = None
    upcoming_contests = None

    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.leetcode_username:
            leetcode_data = get_leetcode_stats(profile.leetcode_username)
            upcoming_contests = get_upcoming_contests()
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Profile not found.')

    return render(request, 'leetcode.html', {'leetcode_data': leetcode_data, 'upcoming_contests': upcoming_contests})

# CodeChef Page
@login_required
def codechef_view(request):
    profile = None
    codechef_data = None

    try:
        profile = UserProfile.objects.get(user=request.user)
        print(f"Profile found: {profile}")
        print(f"hello:{profile.codechef_username}")
        if profile.codechef_username:
            print("hello")
            print(f"CodeChef username: {profile.codechef_username}")
            codechef_data = get_codechef_stats(profile.codechef_username)
            print(f"CodeChef data: {codechef_data}")
            if not codechef_data:
                messages.warning(request, 'No CodeChef data found.')
        else:
            messages.warning(request, 'No CodeChef username found in profile.')
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Profile not found.')

    return render(request, 'codechef.html', {'codechef_data': codechef_data})


@login_required
def codeforces_view(request):
    profile = None
    codeforces_data = None
    upcoming_contests = None

    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.codeforces_username:
            codeforces_data = get_codeforces_rating(profile.codeforces_username)
            upcoming_contests = get_upcoming_codeforces_contests()
            if not codeforces_data:
                messages.warning(request, 'No Codeforces data found.')
        else:
            messages.warning(request, 'No Codeforces username found in profile.')
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Profile not found.')

    return render(request, 'codeforces.html', {'codeforces_data': codeforces_data, 'upcoming_contests': upcoming_contests})

@login_required
def geeksforgeeks_view(request):
    profile = None
    gfg_data = None
    weekly_contests = None

    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.gfg_username:
            gfg_data = fetch_user_profile(profile.gfg_username)
            weekly_contests = fetch_weekly_contests()
            if not gfg_data:
                messages.warning(request, 'No GeeksforGeeks data found.')
        else:
            messages.warning(request, 'No GeeksforGeeks username found in profile.')
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Profile not found.')

    return render(request, 'geeksforgeeks.html', {'gfg_data': gfg_data, 'weekly_contests': weekly_contests})