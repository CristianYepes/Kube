# cub3D — My first RayCaster with miniLibX

**Version: 12.0**

> *Summary: This project is inspired by the world-famous Wolfenstein 3D game, which is considered the first FPS ever created. It will enable you to explore ray-casting. Your goal will be to make a dynamic view inside a maze, where you will have to find your way.*

---

## Chapter I — Foreword

Developed by **Id Software**, led by the world-renowned John Carmack and John Romero, and published in 1992 by **Apogee Software**, **Wolfenstein 3D** is the first true "First Person Shooter" in the history of video games.

Wolfenstein 3D is the ancestor of games like Doom (Id Software, 1993), Doom II (Id Software, 1994), Duke Nukem 3D (3D Realm, 1996) and Quake (Id Software, 1996), that are additional eternal milestones in the world of video games.

Now, it's your turn to relive History...

> The game Wolfenstein 3D originally takes place in the Nazi Germany, which could be potentially disturbing. Pictures and history of this game are only brought to you for technical reasons and pop/geek culture reasons, as the game was considered as a masterpiece for both.

---

## Chapter II — Goals

This project's objectives are similar to all this first year's objectives: rigor, use of C, basic algorithms, information research, etc.

As a graphic design project, cub3D will enable you to improve your skills in these areas: windows, colors, events, fill shapes, etc.

In conclusion, cub3D is a remarkable playground to explore the playful practical applications of mathematics without having to understand the specifics.

With the help of numerous documents available on the internet, you will use mathematics as a tool to create elegant and efficient algorithms.

---

## Chapter III — Common Instructions

- Your project must be written in C.
- Your project must be written in accordance with the Norm. If you have bonus files/functions, they are included in the norm check, and you will receive a 0 if there is a norm error.
- Your functions should not quit unexpectedly (segmentation fault, bus error, double free, etc.) except for undefined behavior. If this occurs, your project will be considered non-functional and will receive a 0 during the evaluation.
- All heap-allocated memory must be properly freed when necessary. Memory leaks will not be tolerated.
- If the subject requires it, you must submit a Makefile that compiles your source files to the required output with the flags `-Wall`, `-Wextra`, and `-Werror`, using `cc`. Additionally, your Makefile must not perform unnecessary relinking.
- Your Makefile must contain at least the rules `$(NAME)`, `all`, `clean`, `fclean` and `re`.
- To submit bonuses for your project, you must include a **bonus** rule in your Makefile, which will add all the various headers, libraries, or functions that are not allowed in the main part of the project. Bonuses must be placed in `_bonus.{c/h}` files, unless the subject specifies otherwise. The evaluation of mandatory and bonus parts is conducted separately.
- If your project allows you to use your libft, you must copy its sources and its associated Makefile into a `libft` folder. Your project's Makefile must compile the library by using its Makefile, then compile the project.
- We encourage you to create test programs for your project, even though this work **does not need to be submitted and will not be graded**. It will give you an opportunity to easily test your work and your peers' work. You will find these tests especially useful during your defence. Indeed, during defence, you are free to use your tests and/or the tests of the peer you are evaluating.
- Submit your work to the assigned Git repository. Only the work in the Git repository will be graded. If Deepthought is assigned to grade your work, it will occur after your peer-evaluations. If an error happens in any section of your work during Deepthought's grading, the evaluation will stop.

---

## Chapter IV — AI Instructions

### Context

During your learning journey, AI can assist with many different tasks. Take the time to explore the various capabilities of AI tools and how they can support your work. However, always approach them with caution and critically assess the results. Whether it's code, documentation, ideas, or technical explanations, you can never be completely sure that your question was well-formed or that the generated content is accurate. Your peers are a valuable resource to help you avoid mistakes and blind spots.

### Main message

- Use AI to reduce repetitive or tedious tasks.
- Develop prompting skills -- both coding and non-coding -- that will benefit your future career.
- Learn how AI systems work to better anticipate and avoid common risks, biases, and ethical issues.
- Continue building both technical and power skills by working with your peers.
- Only use AI-generated content that you fully understand and can take responsibility for.

### Learner rules

- You should take the time to explore AI tools and understand how they work, so you can use them ethically and reduce potential biases.
- You should reflect on your problem before prompting -- this helps you write clearer, more detailed, and more relevant prompts using accurate vocabulary.
- You should develop the habit of systematically checking, reviewing, questioning, and testing anything generated by AI.
- You should always seek peer review -- don't rely solely on your own validation.

### Phase outcomes

- Develop both general-purpose and domain-specific prompting skills.
- Boost your productivity with effective use of AI tools.
- Continue strengthening computational thinking, problem-solving, adaptability, and collaboration.

### Comments and examples

- You'll regularly encounter situations -- exams, evaluations, and more -- where you must demonstrate real understanding. Be prepared, keep building both your technical and interpersonal skills.
- Explaining your reasoning and debating with peers often reveals gaps in your understanding. Make peer learning a priority.
- AI tools often lack your specific context and tend to provide generic responses. Your peers, who share your environment, can offer more relevant and accurate insights.
- Where AI tends to generate the most likely answer, your peers can provide alternative perspectives and valuable nuance. Rely on them as a quality checkpoint.

**Good practice:** I ask AI: "How do I test a sorting function?" It gives me a few ideas. I try them out and review the results with a peer. We refine the approach together.

**Bad practice:** I ask AI to write a whole function, copy-paste it into my project. During peer-evaluation, I can't explain what it does or why. I lose credibility -- and I fail my project.

**Good practice:** I use AI to help design a parser. Then I walk through the logic with a peer. We catch two bugs and rewrite it together -- better, cleaner, and fully understood.

**Bad practice:** I let Copilot generate my code for a key part of my project. It compiles, but I can't explain how it handles pipes. During the evaluation, I fail to justify and I fail my project.

---

## Chapter V — Mandatory part - cub3D

| Field | Value |
|---|---|
| **Program Name** | `cub3D` |
| **Files to Submit** | All your files |
| **Makefile** | `all`, `clean`, `fclean`, `re`, `bonus` |
| **Arguments** | a map in format `*.cub` |
| **External Functions** | `open`, `close`, `read`, `write`, `printf`, `malloc`, `free`, `perror`, `strerror`, `exit`, `gettimeofday`. All functions of the math library (`-lm` man man 3 math). `gettimeofday()`. All functions of the MinilibX library. |
| **Libft authorized** | Yes |
| **Description** | You must create a "realistic" 3D graphical representation of the inside of a maze from a first-person perspective. You have to create this representation using the ray-casting principles mentioned earlier. |

### Constraints

- You **must** use the miniLibX. Either the version that is available on the operating system, or from its sources. If you choose to work with the sources, you will need to apply the same rules for your libft as those written above in Common Instructions part.
- The management of your window must remain smooth: changing to another window, minimizing, etc.
- Display different wall textures (the choice is yours) that vary depending on which side the wall is facing (North, South, East, West).
- Your program must be able to set the floor and ceiling colors to two different ones.
- The program displays the image in a window and respects the following rules:
  - The left and right arrow keys of the keyboard must allow you to look left and right in the maze.
  - The W, A, S, and D keys must allow you to move the point of view through the maze.
  - Pressing **ESC** must close the window and quit the program cleanly.
  - Clicking on the red cross on the window's frame must close the window and quit the program cleanly.
  - The use of **images** of the minilibX library is strongly recommended.
- Your program must take as a first argument a scene description file with the `.cub` extension.

### Map rules

- The map must be composed of only 6 possible characters: **0** for an empty space, **1** for a wall, and **N**, **S**, **E** or **W** for the player's start position and spawning orientation.

  Example of a simple valid map:
  ```
  111111
  100101
  101001
  1100N1
  111111
  ```

- The map must be closed/surrounded by walls, if not the program must return an error.
- Except for the map content, each type of element can be separated by one or more empty lines.
- Except for the map content which always has to be the last, each type of element can be set in any order in the file.
- Except for the map, each type of information from an element can be separated by one or more spaces.
- The map must be parsed as it looks in the file. Spaces are a valid part of the map and are up to you to handle. You must be able to parse any kind of map, as long as it respects the rules of the map.
- Except for the map, each element must begin with its type identifier (composed by one or two characters), followed by its specific information in a strict order:
  - **North texture:**
    ```
    NO ./path_to_the_north_texture
    ```
    - identifier: **NO**
    - path to the north texture

  - **South texture:**
    ```
    SO ./path_to_the_south_texture
    ```
    - identifier: **SO**
    - path to the south texture

  - **West texture:**
    ```
    WE ./path_to_the_west_texture
    ```
    - identifier: **WE**
    - path to the west texture

  - **East texture:**
    ```
    EA ./path_to_the_east_texture
    ```
    - identifier: **EA**
    - path to the east texture

  - **Floor color:**
    ```
    F 220,100,0
    ```
    - identifier: **F**
    - R,G,B colors in range [0,255]: **0, 255, 255**

  - **Ceiling color:**
    ```
    C 225,30,0
    ```
    - identifier: **C**
    - R,G,B colors in range [0,255]: **0, 255, 255**

- Example of the mandatory part with a minimalist `.cub` scene:
  ```
  NO ./path_to_the_north_texture
  SO ./path_to_the_south_texture
  WE ./path_to_the_west_texture
  EA ./path_to_the_east_texture

  F 220,100,0
  C 225,30,0

        1111111111111111111111111
        1000000000110000000000001
        1011000001110000000000001
        1001000000000000000000001
  1111111101100000111000000000001
  1000000001100000111011111111111
  1111011111111011100000010001
  1111011111111011101010010001
  1100000011010101100000010001
  1000000000000001100000010001
  1000000000000001101010010001
  1100000110101011111011110N0111
  11110111 1110101 101111010001
  11111111 1111111 111111111111
  ```

- If any misconfiguration of any kind is encountered in the file, the program must exit properly and return "Error\n" followed by an explicit error message of your choice.

---

## Chapter VI — Readme Requirements

A `README.md` file must be provided at the root of your Git repository. Its purpose is to allow anyone unfamiliar with the project (peers, staff, recruiters, etc.) to quickly understand what the project is about, how to run it, and where to find more information on the topic.

The `README.md` must include at least:

- The very first line must be italicized and read: *This project has been created as part of the 42 curriculum by <login1>[, <login2>[, <login3>[...]]]*
- A "**Description**" section that clearly presents the project, including its goal and a brief overview.
- An "**Instructions**" section containing any relevant information about compilation, installation, and/or execution.
- A "**Resources**" section listing classic references related to the topic (documentation, articles, tutorials, etc.), as well as a description of how AI was used -- specifying for which tasks and which parts of the project.
- **Additional sections may be required depending on the project** (e.g., usage examples, feature list, technical choices, etc.).

Any required additions will be explicitly listed below.

> Your README must be written in English.

---

## Chapter VII — Bonus part

> **Bonuses will be evaluated only if your mandatory part is perfect. By perfect we naturally mean that it needs to be complete, that it cannot fail, even in cases of nasty mistakes such as incorrect usage, etc. It means that if your mandatory part does not obtain ALL the points during the grading, your bonuses will be entirely IGNORED.**

Bonus list:

- Wall collisions.
- A minimap system.
- Doors which can open and close.
- Animated sprites.
- Rotate the point of view with the mouse.

> You will be able to create better games later do not waste too much time!

> You are allowed to use other functions or add symbols on the map to complete the bonus part as long as their use is justified during your evaluation. You are also allowed to modify the expected scene file format to fit your needs. Be smart!

---

## Chapter VIII — Examples

*(See the PDF for visual examples of:)*
- Wolfenstein3D original design replica, using RayCasting.
- Example of what your project could look like as per the mandatory part.
- Example of the bonus part with a minimap, floor and ceiling textures, and an animated sprite.
- Example of a bonus with a HUD, health bar, shadow effect and weapon that can shoot.
- Example of a bonus game with a weapon and the player looking at the ceiling.

> Note: This document may contain copyrighted images. We consider that this subject, created for educational purpose, falls under the Fair Use guidelines.

---

## Chapter IX — Submission and peer-evaluation

Submit your assignment to your Git repository as usual. Only the work inside your repository will be evaluated during the defense. Don't hesitate to double check the names of your files to ensure they are correct.

During the evaluation, a brief **modification of the project** may occasionally be requested. This could involve a minor behavior change, a few lines of code to write or rewrite, or an easy-to-add feature.

While this step may **not be applicable to every project**, you must be prepared for it if it is mentioned in the evaluation guidelines.

This step is meant to verify your actual understanding of a specific part of the project. The modification can be performed in any development environment you choose (e.g., your usual setup), and it should be feasible within a few minutes -- unless a specific timeframe is defined as part of the evaluation.

You can, for example, be asked to make a small update to a function or script, modify a display, or adjust a data structure to store new information, etc.

The details (scope, target, etc.) will be specified in the **evaluation guidelines** and may vary from one evaluation to another for the same project.
