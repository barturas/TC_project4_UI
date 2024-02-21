### This is the beginning of an online music creation app.

The final app should work within a web browser with user authentification, user space, and the ability for a user to upload an audio sample 
for up to X min length, slice that audio sample to the needed number of slices per specific algorithm, e.g., slicing using loudness or beats profile of the audio sample.
Then, the user should be able to adjust (fine-tune the timing) slices. Once the user is finished with slicing, playing slices will be possible using keyboard keys, e.g.
using "a" through the "h" key (6 keys if 6 slices were made).


### Log:
- created a solution for "physical slicing"
    - tested, used keyboard to play separate slices
    - I thought that instead of physical slicing it would be more efficient to use timecodes (start and end) of the original sample to play slice.
- rewrote code to use timecodes for slicing
- implemented simple UI for uploading audio sample
- for now, the default number of slices will be 9 (later this will be adjusted for a user to decide)
- added possibility for a user to choose no. of slices on file loading.

## Usage:

Run `main.py`.
Select `Number of slices` and `Load Audio File`

