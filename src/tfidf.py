import os
import sys
import math
import collections

import ashlib.util.vector

class TFIDFCalculator(object):

    def __init__(self):
        self.documentFrequencies = None

    def calibrate(self, corpus):
        # |corpus| should be a list of sentences, each of which is a list of words
        self.documentFrequencies = collections.Counter()
        for document in corpus:
            words = set(document)
            for word in words:
                self.documentFrequencies[word] += 1

    def normalizedTermFrequencyVector(self, sentence):
        # |sentence| should be a list of words.

        vector = {}

        # Count occurrences
        for word in sentence:
            if word in vector:
                vector[word] += 1.0
            else:
                vector[word] = 1.0

        # Normalize
        for word in vector:
            vector[word] /= float(len(sentence))

        return vector

    def inverseDocumentFrequency(self, word):
        documentFrequency = self.documentFrequencies[word]
        idf = 1.0
        if documentFrequency > 0.0:
            idf += math.log(self.corpusSize / documentFrequency)
        return idf

    def inverseDocumentFrequencyVector(self, sentence):
        # |sentence| should be a list of words
        vector = {}
        for word in sentence:
            vector[word] = self.inverseDocumentFrequency(word)
        return vector

    def tfidfVector(self, sentence):
        tfVector = self.normalizedTermFrequencyVector(sentence)
        idfVector = self.inverseDocumentFrequencyVector(sentence)
        return ashlib.util.vector.product(ashlib.util.vector.product(tfVector, idfVector), self.weights, default=1.0)

    def cosineSimilarity(self, query, referenceIndex, intersectionOnly=True):
        query = self.textProcessor.removeStopWords(query)
        reference = self.textProcessor.removeStopWords(self.corpus[referenceIndex])

        if intersectionOnly:
            # We modify the reference so that it only
            # contains words in the query.
            modifiedReference = []
            for word in reference:
                if word in query:
                    modifiedReference += [word]
            reference = modifiedReference

        queryVector = self.tfidfVector(query)
        referenceVector = self.tfidfVector(reference)

        if ashlib.util.vector.modulus(queryVector) == 0 or ashlib.util.vector.modulus(referenceVector) == 0:
            return 0.0
        else:
            return ashlib.util.vector.cosine(queryVector, referenceVector)

    def angleSimilarity(self, query, referenceIndex, intersectionOnly=True):
        cos = self.cosineSimilarity(query, referenceIndex, intersectionOnly)
        if cos < -1.0: cos = -1.0
        if cos > 1.0: cos = 1.0
        return math.acos(cos)

    def cosineSimilarityBetweenReferences(self, firstReferenceIndex, secondReferenceIndex):
        query = self.textProcessor.removeStopWords(self.corpus[firstReferenceIndex])
        reference = self.textProcessor.removeStopWords(self.corpus[secondReferenceIndex])

        if firstReferenceIndex in self.cache:
            queryVector = self.cache[firstReferenceIndex]
        else:
            queryVector = self.tfidfVector(query)
            self.cache[firstReferenceIndex] = queryVector

        if secondReferenceIndex in self.cache:
            referenceVector = self.cache[secondReferenceIndex]
        else:
            referenceVector = self.tfidfVector(reference)
            self.cache[secondReferenceIndex] = referenceVector

        if ashlib.util.vector.modulus(queryVector) == 0 or ashlib.util.vector.modulus(referenceVector) == 0: cos = 0.0
        else: cos = ashlib.util.vector.cosine(queryVector, referenceVector)
        if cos < -1.0: cos = -1.0
        if cos > 1.0: cos = 1.0
        return cos
