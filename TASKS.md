# TASKS:
## Build a movie list database like IMDB. The page should contain:
    ```
    - Landing page (./landing)
    - Home page (./home)
    - Movie search output page (./search)
    - Specific movie's information page (./movie/<title id>).
    ```
### The Web app will be branded as `MovieVerse`
### 1. Landing page:
- The landing page should have a glowing line like it's the event horizon of a blackhole and the background should have soft glow with star glitter.
- Above that will be the title "MovieVerser" with small description below it, "Unfolding the universe of movies". Below them is Getting Started button.
- Make a circular custom cursor that move softly, smoothly, it will move slower than actual cursor (device's cursor).
For references, check LandingPage_Example.png
### 2. Home page:
- Persistent Search Bar: Always visible at the top, so users can immediately search.
- Featured section which will show top rating movies, 20 of them will be shown here.
- Genre sections: Show popular genres (20 movies each)
    - Action
    - Drama
    - Animation
    - Sci-fi
    - Horror
    - Comedy
    - Romance
### 3. Movie search output page
- Filters & Quick Access
    - Genre chips/tags (e.g., Action, Sci-Fi, Romance).
    - Year slider or “2020s / 2010s / 2000s” clickable shortcuts.
- And show result as cards
### 4. Specific movie's information page
- Show all information about movie:
    - Poster
    - Title
    - Original Title
    - Year (Release)
    - Screen time
    - Rating
    - Votes (Rating count)
    - Director
    - Writer(s)
    - Casts
    - Plot
    - Genres
    - Tags
    - Keywords
    - MPA rating
    - MPA rated reason
    - Awards
    - Language(s)
    - Production companies
    - Production countries
- Trailer zone: use `iframe` for Youtube link and use button `Watch trailer on IMDb` as fallback version in case link unavailable.
- Comment section
### Movie Cards
- Show poster
- Title
- Year
- Screen time
- Rating
- Genres