import sys
import os
import collections

import nltk.stem.wordnet

import ashlib.ml.regressor
import ashlib.ling.corpus
import ashlib.util.maths
import ashlib.ling.stem

# SentenceFeaturizer ########################################


class SentenceFeaturizer(object):

    def __init__(self):
        pass

    def train(self, dataSet):
        # data set-level supervised learning
        pass

    def calibrate(self, document):
        # document-specific unsupervised learning
        pass

    def featurize(self, sentence):
        raise NotImplementedError("Subclasses should override.")

## SentenceFeaturizer #################################################################################

class BOWFeaturizer(SentenceFeaturizer):
    
    def __init__(self):
        pass
    
    def train(self, dataSet):
        # data set-level supervised learning
        pass
    
    def calibrate(self, document):
        # document-specific unsupervised learning
        pass
    
    def featurize(self, sentence):
        return sentence.words

# SentenceQualityPredictor ####################################


class SentenceQualityPredictor(ashlib.ml.regressor.LinearRegressor):

    def __init__(self, sentenceQualityCalculator, sentenceFeaturizer):
        super(SentenceQualityPredictor, self).__init__()
        self.qualityCalculator = sentenceQualityCalculator
<<<<<<< HEAD
        self.featurizer = sentenceFeaturizer
    
=======
        self.featurizer = SentenceFeaturizer()

>>>>>>> aa56f2382652196a04996834b68f7c85c00ac1f7
    def calibrate(self, storyText):
        self.featurizer.calibrate(storyText)

    def predict(self, sentence):
        return ashlib.util.maths.sigmoid(super(
                    SentenceQualityPredictor, self).predict(sentence))

    def featurize(self, sentence):
        self.featurizer.featurize(sentence)

    def train(self, dataSet):
        self.featurizer.train(dataSet)

        sentences = []
        qualityScores = []
        for story in dataSet:
            self.calibrate(story.text)
            self.qualityCalculator.calibrate(story.summary)
            for sentence in story.text.sentences:
                sentences.append(sentence)
                qualityScores.append(
                    self.qualityCalculator.calculate(sentence))

        super(GeneralSentenceQualityPredictor, self).train(
            sentences, qualityScores)

# SentenceQualityCalculator ################################################


class SentenceQualityCalculator(object):
    def __init__(self):
        pass

    def preprocess(self, words):
        words = ashlib.ling.stem.lemmatize(words)
        return ashlib.ling.corpus.removeStopWords(words)

    def calibrate(self, summary):
        raise Error("Subclasses should override.")

    def calculate(self, sentence):
        raise Error("Subclasses should override.")

# PrecisionQualityCalculator ########################


class PrecisionQualityCalculator (SentenceQualityCalculator):
    def __init__(self):
        super(PrecisionQualityCalculator, self).__init__()
        self.summaryWords = None

    def calibrate(self, summary):
        self.summaryWords = set(self.preprocess(summary.words()))

    def calculate(self, sentence):
        # TODO: could add brevity penalty, or just \
        #    straight up make this use BLEU
        words = self.preprocess(sentence.words)
        precision = 0.0
        for word in words:
            if word in self.summaryWords:
                precision += 1
        precision /= len(words)
        return precision

# SimilarityQualityCalculator ########################################


class SimilarityQualityCalculator(SentenceQualityCalculator):
    def __init__(self, sentenceSimilarityCalculator):
        super(SimilarityQualityCalculator, self).__init__()
        self.similarityCalculator = sentenceSimilarityCalculator
        self.summarySentences = None

    def calibrate(self, summary):
        self.summarySentences = summary.sentences()
        self.similarityCalculator.calibrate(summary.sentences())

    def calculate(self, sentence):
        maxSimilarity = float("-inf")
        for summarySentence in self.summarySentences:
            similarity = self.similarityCalculator.calculate(
                sentence, summarySentence)
            if similarity > maxSimilarity:
                maxSimilarity = similarity
        return maxSimilarity
