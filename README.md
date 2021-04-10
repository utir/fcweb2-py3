# fcweb - Explainable fact checker


## Setup
From your terminal...

    1. Clone the repository and navigate to the folder
        a. git clone https://github.com/anubrata/fcweb-2.git
        b. cd fcweb-2
    2. Setup your virtual environment, install the packages, and activate it
        a. python3 -m venv venv
        b. source venv/bin/activate
        c. pip install -r requirements.txt
    3. Start the project!
        a. python setup.py
        b. python run.py
     
## Instructions 
This web app uses many different routes that contain different parameters that are passed to a modular HTML file that will display different experimental features.

The creation of each modular experiment group is handled in `routes.py` with the `load_route_response()` function. This function creates the response object that will be displayed to the user. These dynamic parameters are:

 1. `static_stance`: Setting this to true will show a user the AI predicted stance of an article, however they will not be able to edit this.
 2. `dynamic_stance`: Setting this to true will show a user the AI predicted stance, however, a user will have the option to chance an article's stance if they disagree with this prediction.
 3. `static_reputation`: Setting this to true will show a user the AI predicted reputation of a headline's stance between 0-100%. 0% is a low reputation while 100% is a high reputation.
 4. `dynamic_reputation`: Setting this to true will show a user the AI predicted reputation on a slider. A user will be able to change this slider if they believe a source should have a higher/lower reputation.
 5. `veracity_prediction`: Setting this to true will add a visual indicator of whether the combination of sources and their reputations show that a claim is true or false. This indicator is a slider that shows the percent chance that the claim is true and the percent chance that it is false.
 6. `static_bias`: Setting this to true will add a visual indicator next to each headline that shows the political bias of a source (Liberal, Leans Liberal, Centrist, Leans Republican, Republican)
 7. `bias_prediction`: Setting this to true will add a visual indicator that shows whether the prediction given by the veracity predictor is biased towards liberal headlines or conservative headlines. For example, if a user gives a high reputation to liberal sources and a low reputation to conservative sources, the veracity prediction given is biased liberally.
 8. `amazon_url`: This parameter is a string which sets the url where the form submits to.

These parameters are then passed to `modular-experiment.html`. This file is written in HTML and jQuery, and is largely straightforward. A user is shown a consent form, then a brief survey about their practices assessing truthfulness of online claims, instructions on how to work the web app, and afterwards are taken to the actual experiment. Depending on the combination of parameters described above, different blocks of code will be displayed to the user. 

Within the jQuery code at the bottom of the page, there are several functions that handle loading data and updating the page with new information. These methods are:

 1. `shuffle(array)`: This code uses a simple algorithm to randomize the order in which users are shown headlines in order to reduce bias in our final data collected.
 2. `loadForm(claim_id)`: This function generates the form inputs for each individual claim. For each claim, users are asked to assess the truthfulness of the claim, how strongly they feel about their prediction, and explain their response. New form elements are added for each claim so that mturk is able to keep track of all responses.
 3. `eval_vera()` and `eval_bias()`: These methods are used to calculate the ratios between whether a claim is true or false and whether a prediction is biased liberally or conservatively. They are called whenever a new claim is presented, or if a user modifies a page element that would influence the predictions.
 4. `logTime(position, time)`: This method adds a form element that marks the time it takes a user to complete a certain part of the experiment. For example, if a user takes 5 seconds to read the consent form, this method adds a form input that contains that time so that we can track it later on mturk.
 5. `getHeadlines(claim_id)`: This method is used to load the articles associated with a certain claim. 

Lastly, the functionality of the page is mainly contained within the `$(document).ready(` function. The code within here will load the data, popovers, start the timer, while also adding listeners for the buttons and form elements on the page so that they respond to user input.  
