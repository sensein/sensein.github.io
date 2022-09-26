# Discrimination in Artificial Intelligence for Voice Applications


<!-- History/Rationale of AI  -->
### AI History
The notion of Artificial Intelligence (AI) has been scrutinized throughout history. For instance, classical philosophers [attempted](https://medium.com/@cstegman/what-plato-has-taught-me-about-artificial-intelligence-3a17f31a5805) to represent human knowledge and intelligence using symbolic abstractions. Indeed, the first official spark of understanding whether machines could think was ignited by Vannevar Bush’s seminal article [*'As We May Think'*](http://worrydream.com/refs/Bush%20-%20As%20We%20May%20Think%20(Life%20Magazine%209-10-1945).pdf) in 1945, in which he had foreseen how the future could benefit from amplifying human knowledge using man-made machines. Subsequently, in 1950, Alan Turing proposed a [logical framework](https://www.csee.umbc.edu/courses/471/papers/turing.pdf) to build and test intelligent machines, paving the road for John McCarthy to coin the term *Artificial Intelligence* in the [first conference](https://www.aaai.org/ojs/index.php/aimagazine/article/view/1904/1802) concerning this subject in 1956.

<!-- Applications/Usages for AI  -->
One rationale behind building AI systems is to mimic human intelligence and behavior, and now, scientists’ anticipations for the benefits of AI are being realized. These benefits are manifested in the surge of AI applications serving vast disciplines (e.g. healthcare, legal system, business,…etc). Whereas, the ramifications of replicating human behavior and building anthropomorphic machines haven’t been fully questioned yet.

*Is it ideal to build a computational abstract simulating human intelligence?*

*Will AI systems inherit/mirror human prejudice?*

### Gender and Racial Disparities in AI

<!-- Disparities in AI  -->
Many questions about racial and gender disparities have been raised recently given the ample empirical evidence highlighting them in AI models. Discrepancies in the performance of deep learning (DL) models due to race and gender have been a trending topic. Despite the inflation in the number of neural networks published to solve demanding tasks using diverse modalities (e.g. image, text, audio, and graphs), it has been occasionally noted that these models are molded with racial and gender biases. For instance, previous studies pointed out discrepancies in [facial biometric](https://proceedings.mlr.press/v81/buolamwini18a/buolamwini18a.pdf) systems, showing that classifiers performed best on male subjects with lighter skin and worst on female subjects with darker skin. In the case of predictive algorithms, a software called [COMPAS](https://en.wikipedia.org/wiki/COMPAS_(software)) is widely used as a risk assessment tool for criminals. It was reported that this [software](https://mit-serc.pubpub.org/pub/risk-prediction-in-cj/release/1), favored white defendants over black defendants when deciding whether the defendant will commit the same crime again or not. This software generated significantly more false positives for black defendants compared to white ones, as illustrated in Figure 1.


| ![compas.png](https://i.imgur.com/59PosVm.png) |
|:--:|
| <b>Fig.1 - COMPAS predictions reported in Dressel and Farid, 2018</b>|

Similarly, in healthcare, racial disparities have been addressed which might yield detrimental effects on diagnosis and access to treatment - for example, a [study](https://www.sciencedirect.com/science/article/pii/S2666389921002026#bib1) highlighted that a model was diagnosing a black patient as healthier than a white patient with the same condition. 

Inevitably, it is foreseeable that we will find gender and racial disparities in voice-based deep learning models. For instance, automatic speech recognition (ASR) systems have shown discrepancies in word error rate (WER) across [race](https://www.pnas.org/doi/pdf/10.1073/pnas.1915768117) and [gender](http://www.ethicsinnlp.org/workshop/pdf/EthNLP06.pdf). WER results for race and gender are shown in Figures 2 and 3, respectively.

| ![race.png](https://i.imgur.com/zenkHY3.png) |
|:--:|
| <b>Fig.2 - WER reported in Koenecke et al., 2020</b>|

| ![gender.png](https://i.imgur.com/31xNcKd.png) |
|:--:|
| <b>Fig.3 - WER reported in Tatman, 2017</b>|

These striking examples expose our lack of ability to interpret neural networks and how they learn. One might guess that the main goal when developing a state-of-the-art DL model, is to only improve accuracies without considering the consequences. To better address these issues, we need to focus more on understanding the learning paradigm itself along with the datasets considered for training.

<!-- All these examples lay bare our lack of interpretation of the neural networks’ learning process. One might hypothesize that the main focus, when developing a novel DL model, is to improve their learning process to yield striking accuracies without considering the consequences of such a learning paradigm, datasets considered for training and unraveling this enigma. -->


A recent study was published discussing racial and gender disparities in [voice biometric systems](https://www.nature.com/articles/s41598-022-06673-y.pdf) which we will dive into deeper in this blog.

### Racial and Gender disparities in Voice Biometrics

<!-- Summarize the paper -->
[Chen et al.](https://www.nature.com/articles/s41598-022-06673-y.pdf) created a matched corpus of non-speech voice recordings from 300 speakers. The speakers were balanced in terms of their racial profile (i.e. White, Black, Latinx, and Asian) and gender (i.e. Male and Female). Firstly, they extracted, from the compiled dataset, inherent voice characteristics encompassing temporal, spectral, cepstral, and entropy-related acoustic features. Then, they evaluated the aforementioned features (15 features) across racial and gender subgroups, demonstrating significant differences across gender subgroups in most features, except for $\Delta$ MFCC, Perm entropy, and SVD entropy. Conversely, across racial subgroups, they observed a small number of features that showed significant differences (e.g. F0, F1, F2, PDF entropy, and Perm entropy). Their work pipeline is presented in Figure 4.

| ![system.png](https://i.imgur.com/FhT4PQr.png) |
|:--:|
| <b>Fig.4 - Taken from Chen et al., 2022</b>|

In the second part of their study, they evaluated speaker identification performance of different voice biometric models (e.g. MS Azure, 1D CNN, TDNN, ResNet18, ResNet34, and AutoSpeech). The authors found that the top 3 models (ResNet18, ResNet34, and AutoSpeech) yielded significant differences across racial and gender subgroups that are worse for Latin subjects and males in general, as shown in Figures 5 and 6, leading them to hypothesize that the main causal factor for gender disparities is inherent vocal characteristics, as illustrated above, in addition to the models' bias. Whereas, the main causal factor for racial disparities is the features extracted from DL models.

| ![race_chen.png](https://i.imgur.com/XQrq0x6.png) |
|:--:|
| <b>Fig.5 - Reported performance from Chen et al., 2022</b>|

| ![gender_chen.png](https://i.imgur.com/x1PpPGC.png) |
|:--:|
| <b>Fig.6 - Reported performance from Chen et al., 2022</b>|

### Gender Disparity

[Chen et al.](https://www.nature.com/articles/s41598-022-06673-y.pdf) reported that the main causal factor for gender disparity is caused by the variability in voice properties across men and women. This statement could be further endorsed by investigating the physiological differences between gender. 

#### Physiological-based Differences

For instance, for us to speak, we first need to make a sound with our vocal folds (VFs). Air comes from the lungs and passes through the vocal folds making them oscillate which creates a tone, as demonstrated in the lower part of Figure 7. This process is called phonation. The oscillation frequency is called fundamental frequency (f0) and is perceived as pitch. The pitch of phonation is determined as a response to the change of VFs’ elasticity and tension.

| ![mri.png](https://i.imgur.com/Ytj59yP.gif) |
|:--:|
| <b>Fig.7 - MRI scan of someone speaking ([source](https://www.lakewoodamdc.co.uk/))</b>|

Projecting this information to gender, adult males have, on average, longer and thicker VFs compared to adult females, yielding slower VF vibration (lower F0) and perceptually low-pitched. On the other hand, adult female VFs are relatively shorter and thinner, producing faster VF vibration (higher F0) which is perceived as high-pitched.

Similarly, adult males typically have longer vocal tracts than females. The effect of these physiological differences is translated into sex-based extracted acoustic features. It is worth mentioning that the acoustic signals generated are highly dependent on the geometry of the vocal tract, vocal and nasal cavities, and VFs. However, several studies have shown that other physiological data (e.g. height and weight) have a weak correlation with the perceptual outcome ([Hollien and Jackson, 1973](https://www.sciencedirect.com/science/article/pii/S0095447019314160); [Kunzel, 1989](https://pubmed.ncbi.nlm.nih.gov/2608725/); [Van Dommelen and Moxness, 1995](https://pubmed.ncbi.nlm.nih.gov/8816083/); [Collins, 2000](https://www.sciencedirect.com/science/article/abs/pii/S0003347200915239?via%3Dihub); [Gonzales, 2004](https://www.sciencedirect.com/science/article/pii/S0095447003000494?via%3Dihub)).

#### Cultural-based Differences

Based on these studies, researchers started to consider other influences beyond physiological features that impact perceptual features. Indeed, they found cultural influences on speaking pitch levels ([Deutsch et al. (2009)](https://pubmed.ncbi.nlm.nih.gov/19425624/)). This means that long-term exposure to a specific community might create a mental representation for a speaker influencing their pitch levels, suggesting that cultural factors have as much impact (or maybe higher) on perceptual output as physiological representations. In a similar vein, studying the prosodic features of gender-neutral interactional particles in the Japanese language such as *ne* and *yo*, [Hiramoto-Sanders (2002)](http://journals.linguisticsociety.org/proceedings/index.php/BLS/article/view/3826/3526) found that more prosody is expressed in feminine speech compared to masculine ones.

Thus, the difference in vocal inherent characteristics, in the paper, might mirror socio-cultural and physiological variabilities between gender.

#### Model-based Differences

As shown in Figure 6, four out of six models featured gender disparities. MS Azure performed significantly better on male subjects than on female subjects. On the other hand, the top three models performed worst on male subjects. Although the inputs to the six models were consistent, the performances across gender were inconsistent. As a result, [Chen et al.](https://www.nature.com/articles/s41598-022-06673-y.pdf) suggested that the models' extracted features contributed to the observed performance discrepancy. We will further unpack the model-based impact in section *[Dissecting AI Features](##Dissecting-AI-Features)*.

### Racial Disparity

[Chen et al.](https://www.nature.com/articles/s41598-022-06673-y.pdf) indicated that the voice biometric models they studied performed worst on Latinx speakers. As a result, they suggested that the causal factor for racial disparities is predominantly in the features extracted from the DL models.

Unlike gender-dependent voice studies, studying racial groups is more staggeringly complex given that a lot of studies attempted to tackle the same topic but with inconclusive results. The main question here is if the distinguishability of a speaker’s race is due to inherent physiological differences or acquired dialectal differences. As [Kreiman and Sidtis (2011)](https://books.google.com/books?hl=en&lr=&id=w4v2GujpazQC&oi=fnd&pg=PA237&dq=kreiman+and+sidtis&ots=EdnlkImCl_&sig=nnpkz6oloqZp6YnkWYXE1zTjIqg#v=onepage&q=kreiman%20and%20sidtis&f=false) mentioned that if it was the former, then, racial identity is consistently molded in a speaker’s speech. Whereas, if it is the latter, then, racial identity might vary across speakers depending on their dialectal exposure.

#### Physiological-based Differences

There has been contradictory data regarding physiological differences across races. For instance, [Xue et al. (2009)](https://www.tandfonline.com/doi/pdf/10.1080/02699200500297716?needAccess=true) evaluated the vocal tract morphological differences of adult male speakers from three different racial populations (White
American, African American, and Chinese). Their findings suggest that there is a significant difference in total vocal tract volume and oral volume across the three racial groups. Also, Chinese subjects featured different overall vocal tract configurations relative to their White and African American cohorts. It is worth mentioning that the subjects were recorded uttering the neutral /ɑ/ sound to alleviate the effect of language or dialect. Furthermore, [Walton et al. (1994)](https://pubs.asha.org/doi/abs/10.1044/jshr.3704.738) reported that the human accuracy of speaker race identification from a sustained /ɑ/ vowel uttered by 50 white and 50 black males is above chance, suggesting that black speakers had higher amplitude and frequency perturbations relative to their counterparts. In addition to a significantly lower harmonics-to-noise ratio.

Conversely, [Ajmani (1990)](https://pubmed.ncbi.nlm.nih.gov/2081705/) reported no significant differences in laryngeal sizes between adult Nigerians of both European or African descent. Also, [Xue and Fucci (2000)](https://journals.sagepub.com/doi/pdf/10.2466/pms.2000.91.3.951) observed no significant acoustic differences between 44 Caucasian American elderly speakers and 40 African American elderly speakers, suggesting that most acoustic parameters are highly sex-dependent.

Building on all previous studies, it is safe to say that there is quite uncertainty when it comes to the significance of vocal variability across racial groups, highlighting the lack of studies considering the interplay across physiological, acoustic, and perceptual components. However, it should be incentivized to further probe and design appropriate experiments for such questions to elucidate if the racial differences in voice are physiologically ingrained or learned in dialect. Also, it might affect our understanding of treatment approaches for different racial groups. [Radowsky et al.](https://www.sciencedirect.com/science/article/abs/pii/S0039606012002887) observed disparities across races after thyroid and parathyroid surgeries yet with an unclear causal explanation.

Surprisingly, [recent work](https://www.thelancet.com/journals/landig/article/PIIS2589-7500(22)00063-2/fulltext) by a group at MIT showed that AI models were capable of predicting self-reported race from different imaging modalities (X-ray imaging, CT chest imaging, and mammography) with high performance indicating that these models captured racial-based physiological features.



That being said, would any disparities/similarities in inherent vocal characteristics across racial groups, reported by Chen et al., be due to dialectal differences, or the variations of physiological data across speakers might play a role here?

#### Cultural-based Differences

As briefly mentioned with gender disparity, culture may play a role in vocal differences. [Deutsch et al.](https://pubmed.ncbi.nlm.nih.gov/19425624/) examined females’ pitch levels in two Chinese villages, showing that they significantly differed by approximately three semitones although they shared the same race, language, and dialect. This experiment suggested that F0 production could reflect a learned representation acquired through linguistic exposure in a community.


#### Model-based Differences

As stated in the beginning, it is suggested that the features extracted from the models are the predominant factor for the observed disparities. As shown in Figure 5, five out of six models performed worst on Latinx subjects compared to their counterparts with different levels of significance, emphasizing the inconsistencies in the models' performances.

They make the argument that Latinx speakers feature lower F1 values in comparison to White speakers ([Xue et al., 2006](https://www.tandfonline.com/doi/pdf/10.1080/02699200500297716?needAccess=true)), suggesting that the DL models are not capable of identifying the F1 band in Latinx speakers, hence the degraded performance. However, when measuring the F1 values on the matched dataset, one can notice the huge overlap in the F1 distributions between White and Latinx speakers, as shown in Figure 8, which might contradict the aforementioned assumption.

With this in mind, the yielded performance could then be justified by saying that the DL models exacerbated the slight differences in acoustic features, leading to obvious disparities. Nevertheless, it could be argued that the reported explanation for racial disparities, in the paper, might need more unpacking to further understand the models' behavior.

*Why would models feature disparities with varying levels of significance?*

|                                   ![racial_f0/1.png](https://i.imgur.com/mFp0EY9.png)                                   |
|:-----------------------------------------------------------------------------------------------------------------------:|
| <b>Fig.8 - Reported F0 and F1 values across races *(W: White, B: Black, A: Asian, L: Latinx)* from Chen et al. 2022</b> |

### Dissecting AI Features

During training, DL models learn to optimize for a specific task or a loss function by transforming input features into task-related labels. This process is carried out by feeding samples from a dataset to the model. The architecture of the DL model determines its complexity and the type of information (e.g. sequences, patterns, local/global features, etc.) learned by the model. That being said, the performance of any DL model majorly depends on:

*i) the dataset fed to the model
ii) the format of the input 
iii) the model's architecture 
iv) the optimization function.*

To further sift through the reasons behind the models' biases and disparities, it is important to investigate the contribution of each of the mentioned factors to the final outcome. In the next section, we shed some light on the impact of datasets used for evaluation and pre-training on models' performance.

<!-- We have discussed above the difficulty of creating an inclusive dataset that could allegedly alleviate the observed disparities. -->

#### Non-speech voice snippets and Inclusive Datasets

Chen et al. proposed a matched dataset including speakers from both genders and four different races. Additionally, they compiled the non-speech voice snippets from the [mPower dataset](https://pubmed.ncbi.nlm.nih.gov/26938265/). The rationale behind collecting only non-speech snippets was to alleviate the linguistic and accent effects on the voice. This line of research has been endorsed for the latter reason and security reasons as well, to have recordings that are not quite identifiable ([Poddar et al., 2017](https://ietresearch.onlinelibrary.wiley.com/doi/epdf/10.1049/iet-bmt.2017.0065)). Accordingly, the authors have selected the voice snippets of speakers uttering the /ɑ/ vowel for 10 seconds, suggesting that this vowel has the most occurrences compared to other syllables. That being said, they found visible disparities in the performance of the models as discussed. As mentioned before, they pointed out that Latinx speakers feature lower F1 during /ɑ/ phonation compared to White/Caucasian speakers ([Xue et al., 2006](https://www.tandfonline.com/doi/pdf/10.1080/02699200500297716?needAccess=true)), implying that the discrepancy in performance affecting Latin speakers might be due to the technical gap in the models’ feature extractors.

Before making the claim against models' biases, it is crucial to question the format of the input fed to the model. For instance, the authors focused on the /ɑ/ phonation as a way of benchmarking the performance of DL models. However, it is intuitive that Latin speakers would feature lower F1 given that the *ae* sound doesn't exist in the Spanish language. Consequently, the phonation of /ɑ/ would be significantly different between Latin and White speakers, triggering a question: how can we compare F1 or other acoustic features across races although they have different vowel inventories?

We might be using an already biased dataset for evaluation since the selected vowel is not neutral across different races.

One might argue that the reported performances could be phoneme-dependent. Would the models maintain the same performance discrepancy if the speakers uttered different phonemes? or would the models disadvantage other racial groups instead? 

However, the reported results might insinuate that the DL models didn't get exposed to different vowel inventories, leading us to explore the datasets used for pre-training the models. In the wake of trying to improve the current DL models to be less biased, most of the studies mentioned usually suggest building more inclusive datasets to help the model learn more generalized features independent of race and gender ([Tatman, 2017](http://www.ethicsinnlp.org/workshop/pdf/EthNLP06.pdf); [Koenecke et al., 2020](https://www.pnas.org/doi/pdf/10.1073/pnas.1915768117); [Chen et al., 2022](https://www.nature.com/articles/s41598-022-06673-y.pdf)). Indeed, aiming for a well-designed dataset might help dampen the disparity issue. Nevertheless, one might argue that it is very challenging to do so. As a matter of fact, it could be infeasible to collect data covering different races, cultures, languages, dialects, etc. and we have seen how people who share the same race and language could still have significant differences in pitch levels ([Deutsch et al., 2009](https://pubmed.ncbi.nlm.nih.gov/19425624/)). And what about people that belong to mixed-race families, would they share physiological/acoustic features similar to a specific race?

Additionally, we have seen the impact of languages on the uttered vowels, as demonstrated in the case of Latin speakers uttering /ɑ/. This could open the door for more questions, for example: would Latin speakers who learned English as a first language show similar acoustic features (e.g. F1) as Latin speakers who acquired the English language later in their life?

Even if we manage to account for between- speaker/gender/race variability, how can we reduce within-speaker variability ([Lavan et al., 2019a](https://journals.sagepub.com/doi/10.1177/1747021819836890); [Lavan et al., 2019b](https://doi.org/10.1111/bjop.12348))? Would the model's performance vary on the same speaker but with a minimal change in the way the speaker is uttering a vowel?

To answer these questions, we need to probe more thoroughly if within-racial groups share physiological, acoustic, or perceptual features. Then, study how to factor out the cultural influence within-groups before attempting to treat the problem as discrete categories of races. To the best of our knowledge, our voices are more of a continuous spectrum and we would always have a margin of error and discrepancy even if we compiled an *inclusive* dataset. [Kathiresan (2022)](https://www.researchgate.net/publication/362546613_Gender_bias_in_voice_recognition_An_i-_and_x-vector-based_gender-specific_automatic_speaker_recognition_study) created gender-balanced training and testing sets from two datasets with different languages (English and Mandarin). Then, he extracted i- and x-vector speaker embeddings to test them in a speaker recognition task. Interestingly, there was still obvious disparities between gender although data samples were balanced during training and testing. This finding might endorse that datasets are not the only factor for biased results.

#### Architecture-based Effects

Besides focusing on datasets, we might need to explore different architectures for speaker identification models. For instance, most of the current models are convolution neural network-based (CNN). CNNs are known for extracting fine-grained and local features from the input data. However, CNNs were traditionally used on images to generate representations covering their spatial components. Over time, CNNs were adapted to work on voice signals by using 2D spectrograms as an equivalent for a 2D image fed to the architecture ([Dieleman et al., 2011](https://archives.ismir.net/ismir2011/paper/000126.pdf)). A spectrogram has a temporal dimension that qualifies it as sequential data ([Palanisamy et al., 2020](https://arxiv.org/pdf/2007.11154.pdf)), hence, some efforts have been made to modify the kernel size in CNNs to go in one direction and account for this temporal sequence ([Chen et al., 2019](https://ieeexplore.ieee.org/document/8683630)). Others complimented the CNN with modules that  capture sequential information such as Recurrent neural networks (RNN) ([Phan et al., 2017](https://arxiv.org/abs/1703.04770)). RNNs are capable of capturing temporal dependencies in sequential data by featuring an internal memory component. Furthermore, others used transformers to extract global and contextual features from audio ([Gulati et al., 2020](https://arxiv.org/abs/2005.08100)).

The level of model complexity and the information learned could highly vary as we continue to augment and modify the architectural bases of feature extractors. Thus, it will be advantageous to break down the problem of model-based discrepancies into architecture-based differences and dataset-based differences. More ablation studies and experiments on such models might boost our understanding of the contributions of the model's facets to the outcome.

### What's Next?

As a result of reporting racial and gender disparities, several documentaries, blogs, and interviews have chewed over this topic from different perspectives (e.g. political, technical, and social). As they all advocate in favor of creating more inclusive datasets, we have argued here that changing the dataset is one aspect of a bigger problem that might not adequately circumvent these disparities. We suggest elaborating on all factors responsible for such outcomes, including datasets, and further pinpointing their contributions. Additionally, understanding the nature of variabilities in gender and race is crucial to better design experiments that account for such differences.

<!-- For instance:

1) **Task/Dataset Protocol:** Would the uttered vowel be equally prevalent across races?
2) 
3) **Model Architecture:**  -->

Finally, acknowledging the limitations of our current models might help alleviate the fear of echoing human prejudice in models. Humans are biased in their nature. Thus, if the ultimate goal is to build anthropomorphic models (human-like), having biased models is an inevitable fate. Although it is argued that we are technically building human-inspired models, not human-like ones, since human-inspired models are models that emulate features from human behavior. Examples of this include CNN layers that learn hierarchical information, self-supervised learning that reinforces common-sense understanding in models, and the concept behind learnable neural networks. That being said, it is a matter of time and effort to eventually disentangle some of the misapprehensions and ramifications concerning AI.

<!-- Then, how did the model learn to be bias although no differences were observed in the acoustic features? Models didn't learn races but learned how to create a non-linear mapping of acoustic features that optimize its objective function. Maybe the model amplified the small frequency differences across races giving rise to a more bias model. I believe they eluded to this issue by showcasing the F1 disparity in the Resnet Models. -->

<!--  
It has been shown that using non-speech snippets is sufficient for identifying a voice and that these snippets didn't feature significant differences across racial groups by studying the vocal characteristics. It might be argued that the racial differences could appear when studying prosodic features that mainly depend on a linguistic signal instead of non-speech signal. Intuitively speaking, linguistic patterns and articulations could easily reveal speaker's demographics including race.

Nevertheless, It is interesting to see in this paper that even though there are no significant differences in vocal characteristics across racial groups some disparities appear when comparing the performance biometric networks based on non-speech samples.

As per the paper's findings, it was observed that only the fundamental and formant frequencies that showed significant differences across racial groups. Concluding that there is no overall observable differences in vocal characteristics across races. Despite that fact yet the models were bias! 

Deep Learning (DL) models basically learn sequences, patterns, local/global features from the input being fed, in that case spectrograms. Thus, the model will only learn information that is provided in the spectrograms. Then, how did the model learned to be bias although no differences were observed in the acoustic features? Models didn't learn races but learned how to create a non-linear mapping of acoustic features that optimize its objective function. Maybe the model amplified the small frequency differences across races giving rise to a more bias model. I believe they eluded to this issue by showcasing the F1 disparity in the Resnet Models.

In my opinion, this finding triggers an important question which is what are these models encoding in the first place? (e.g. what did these models learn during training?). Most of the conclusions stated in the papers presenting gender/racial disparities, including the one discussed, are only focusing on encouraging more inclusive dataset collection to build a well-trained model that observed racial and gender variations [(Tateman, 2017)](http://www.ethicsinnlp.org/workshop/pdf/EthNLP06.pdf) and [(Koenecke, 2020)](https://www.pnas.org/doi/pdf/10.1073/pnas.1915768117). However, this suggestion sounds like a knee-jerk reaction to the problem. Building an inclusive and balanced dataset is an airy-fairy goal basing it on the fact that we need to consider gender and racial vocal variations but then what about vocal variations resulting from sub-racial groups, speakers with mixed races, mental illnesses, respiratory-related diseases...etc? Not to mention the within-speaker variabilities triggered from different speaking-styles, moods, physiological and mental state of the speaker,...etc. Thus, having a bias model is inevitable. Alternatively, we could invest more time to understand the model's limitaions and invariances. We can't solve the problem by adding more data without understanding what the model is encoding, it only puts a band-aid on the problem. Exploring the model's embedding space with the aim to unravel the model's black box could immensely contribute to interpreting deep learning models and give us more control over the encoder's capabilities. 

Additionally, there are plenty of questions and suggestions concerning the model, other than focusing on the input dataset, should be addressed.

1) Does training on spectrograms tunnel vision the model to focus only on spectral features?
2) Is the model's architecture appropriate with the task being addressed (i.e. for any architecture, would adding/removing/modifying a layer impact the model's performance across racial groups)?
3) Would augmenting the input data, trying to isolate the disparity sources, help improve the model's performance?
4) What would be the impact of the mentioned changes on the final embeddings space of the model?


#### Matched Dataset

The claims of any model can only be as clear as the data used to build it. To that end, we noted a few factors with how the populations of this study were matched that are concerning. 

In the "racial dataset" there was an equal number of speakers from each of the racial subgroups (75 per group). However, within each of these groups there was many more males (62) than females (13). Similarly, in the "gender dataset" there were 150 female and 150 male speakers. However, within each of these groups there were many more White speakers (104) than Black, Latinx, or Asian (13, 16, 17, respectively). The smaller number of female speakers in the racial dataset and non-White speakers in the gender dataset means that the measurements from these smaller groups could have low statistical power. This is especially concerning given how many different races are actually represented by each of the larger racial groups, diluting the claims that can actually be made.

Another concern was that some of the participants in this study had diseases that could affect voice quality such as asthma, pneumoia, or bronchitis. It has been shown for conditions such as Vocal Fold Paralysis that these types of diseases can affect measured accoustic features of voice [cite Daniel's paper], which could add significant variability to population measurements of voice features and to the performance of the voice biometric models. Furthermore, the ratio of healthy participants to participants with a disease was not equal among each of the populations. While it appears the intention behind this was to make the population more representative of the real-world, it might have the opposite effect.


#### Accoustic Features
The authors seek to quantiy a ground-truth of voice identity and how it compares between the racial and gender datasets by measurinng a set of 15 features that "represent the essential and primary characteristics of the voice". Unfortunately, there isn't a small, defined set of accoustic features that are agreed upon that can quanitfy a voice identity. This is an area of active research [provide citations such as Kreiman 2021, ]. Furthermore, a challenge in the field has been the proliferaton of disparate accoustic parameters that are not always extracted in the same way, which was the impetus for standards such as the Geneva Minimalistic Acoustic Parameter Set (GeMAPS). While these 15 features likely have something to say about voice identity, using them to establish the ground truth difference between gender or racial groups risks mising important information.


#### Voice Recordings
Limiting the study to an analysis of non-speech voice snippets, specifically to an extended /ɑ/ (‘a’) phoneme has pros and cons. From one standpoint, vocalizing a phoneme should reduce the effects of factors like accent or emotional state of the speaker on the analysis, serving as a an effective control. One vowel also limits us to the configuration of the vocal tract when producing that one vowel. Ideally, this would mean that any differeces seen between race or gender by the biometric models surveyed would be due to inheret model biases, which is our understanding of the author's intent.

However, this does mean that this study is limited in what it can claim about bias. It has been shown that shorter duration speech vocalizations (e.g. from 2.5 minutes to 5 seconds) decreases the accuracy of speaker verification systems [Podday 2018? Pollack 1954?]. It is suggested that this is due an increased variability within the speakers own vocalization, because only a subset of phonemes can be sampled. In other words, the variability of the result from any of these biometric models is likely to be much higher with just an extended vocalization of a vowel versus a longer reading. Furthermore, in recorded speech, context of a phoneme within a word can affect how it is pronounced, implying an extended /ɑ/ (‘a’) might not be properly representative of a participant's voice. Things like accents are also important when talking about the identity of a voice and biases in biometric systems. If a biometric system is more easily fooled by someone with a similar accent to the target speaker among one demographic of speakers than another, this would be a significant real-world security concern.

Because of various concerns with the study design - the nature of the matched populations, the features used to establish similarities and differences, and the recordings themselves, we have a difficult time fully accepting the results of this study. The presence of bias in voice biometric systems would not be a surprise, but further research would be needed.

#### Might skip this
Finally, there does not always appear to be a visually significant difference in performance of some of the models. The two ResNet models and AutoSpeech appear to be fairly close, and given other sources of potential variability in the data previously mentioned, it becomes hard to claim bias. Admitely the Azure model appears to have a lot of variability, but again its hard to say how significant it is?


In Figure 3, it looks like visually a lot of features are similar between the races. It appears the purpose of this is to show that differences in some identity-related metrics exist between races and don't in other metrics. However, all the metrics plotted seem to have similar values across races, and not all fifteen are showm. Given the small sample sizes of the non-white races, it is hard to know if this is a representative sample, especially given the diverse populations contained within each of these macro racial categories.  -->


