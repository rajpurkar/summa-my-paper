import os
import sys
import ntpath
import io
import re

import ashlib.util.file_
import ashlib.util.dir_
import ashlib.util.cache
import ashlib.util.str_
import ashlib.util.list_
import ashlib.ling.tokenize
import ashlib.ling.pos
import ashlib.ling.stem
import ashlib.ling.ner

base_directory = os.path.dirname(os.path.abspath(__file__))
STORIES_DIRECTORY = os.path.abspath(os.path.join(base_directory, "../data/"))
GRIMM_DIRECTORY = os.path.join(STORIES_DIRECTORY, "grimm-stories")
OLD_DIRECTORY = os.path.join(STORIES_DIRECTORY, "old-stories")
WIKIPEDIA_DIRECTORY = os.path.join(STORIES_DIRECTORY, "wikipedia-stories")

META_DATA_FILE_NAME = "metadata.txt"
CONTENT_FILE_NAME = "content.txt"
SUMMARY_FILE_REGEX = "summary\d*.txt"
CACHE_FILE_NAME = "cache.pkl"
ORIGINAL_CACHE_FILE_REGEX = "story\d+\.pkl"

NAME_KEY = "name"
CONTENT_LINK_KEY = "content_link"
SUMMARY_LINK_KEY = "summary_link"

VERBOSE = True

## functions #####################################################################################

def defaultDataSet():
    return DataSet.readCache()

## DataSet #######################################################################################

class DataSet(list):
    
    def parse(self):
        for story in self:
            story.parse()
    
    def partition(self, size, randomize):
        if size > len(self):
            raise Error("Parition cannot be larger than data set.")

        if randomize:
            partition = DataSet()
            partitionIndices = random.sample(list(range(len(self))), partitionSize)
            partitionIndices = sorted(partitionIndices, reverse=True)
            # because the indices are in descending order, removing doesn't alter indices
            for index in partitionIndices:
                partition.append(self[index])
                del self[index]
            return partition
        
        else:
            return self[:size]

    @classmethod
    def fromDirectory(cls, dirPath, readFromCache=False, writeToCache=False, shouldParse=False, modification=None, condition=None):
        set = cls()
        for subDirPath in ashlib.util.dir_.listStdDir(dirPath):
            if condition is None or condition(subDirPath):
                set.append(Story.fromDirectory(subDirPath, readFromCache=readFromCache, writeToCache=writeToCache, shouldParse=shouldParse, modification=modification))
        return set
    
    @classmethod
    def fromDirectories(cls, masterDirPath, readFromCache=False, writeToCache=False, shouldParse=False, modification=None, condition=None):
        set = DataSet()
        for dirPath in ashlib.util.dir_.listStdDir(masterDirPath):
            set.extend(cls.fromDirectory(dirPath, readFromCache=readFromCache, writeToCache=writeToCache, shouldParse=shouldParse, modification=modification, condition=condition))
        return set

    @classmethod
    def modifyCache(cls, dirPath, modification):
        set = cls.fromDirectory(dirPath, readFromCache=True, writeToCache=True, modification=modification)

    @classmethod
    def readCache(cls):
        return cls.fromDirectories(STORIES_DIRECTORY, readFromCache=True)

    @classmethod
    def readWithoutCache(cls):
        return cls.fromDirectories(STORIES_DIRECTORY, readFromCache=False, writeToCache=True)

## Story #########################################################################################

class Story(object):

    def __init__(self, name, content, summaries = []):
        self.name = name
        self.text = content
        self.summaries = summaries
        self.summary = ashlib.util.list_.first(summaries)

    def addSummary(self, summary):
        self.summaries.append(summary)
        self.summary = self.summaries[0]

    def parse(self):
        if VERBOSE: print("Parsing story:", self.name)
        
        self.text.parse()
        for summary in self.summaries:
            summary.parse()
        
        if VERBOSE: print(("Finished parsing story", self.name))

    @classmethod
    def fromDirectory(cls, dirPath, readFromCache=False, writeToCache=False, shouldParse=False, modification=None):
        if readFromCache:
            story = ashlib.util.cache.load(os.path.join(dirPath, CACHE_FILE_NAME))
        
        else:
            name = None
            content = None
            summaries = []
            
            for filePath in ashlib.util.dir_.listStdDir(dirPath):
                fileName = ntpath.basename(filePath)
                
                if fileName == META_DATA_FILE_NAME:
                    for line in ashlib.util.file_.readlines(filePath):
                        if line.find(NAME_KEY + ": ") == 0:
                            name = line[len(NAME_KEY) + 2:].replace("\n", "")
            
                elif fileName == CONTENT_FILE_NAME:
                    content = Document.fromFile(filePath)
                
                elif not re.match(SUMMARY_FILE_REGEX, fileName) is None:
                    summaries.append(Document.fromFile(filePath))

            story = cls(name, content, summaries)
                
        if shouldParse:
            story.parse()

        if modification:
            modification(story)

        if writeToCache:
            ashlib.util.cache.dump(story, os.path.join(dirPath, CACHE_FILE_NAME))
            if VERBOSE: print(("Cached story:", story.name))

        return story

## Document ######################################################################################

class Document(object):
    
    ## TODO: would be good to write some sentence insertion and removal methods. Remember to change indices of affected sentences when do so.

    def __init__(self, content):
        self.__initialContent = content
        self.sentences = []
    
    def parse(self):
        if VERBOSE: print("Parsing document")
        
        sentencesContents = ashlib.ling.tokenize.sentences.tokenizeSentences(ashlib.util.str_.sanitize(self.__initialContent))
        self.sentences = []
        for index, content in enumerate(sentencesContents):
            sentence = Sentence(content, index)
            sentence.parse()
            self.sentences.append(sentence)
        
        if VERBOSE: print("Finished parsing document")

    def content(self): ## TODO: replace with "gloss"
        return " ".join([sentence.content() for sentence in self.sentences])
    
    def words(self):
        return ashlib.util.list_.concatenate([sentence.words for sentence in self.sentences])
    
    def numWords(self):
        return len(self.words())
    
    def numSentences(self):
        return len(self.sentences)
    
    def lemmas(self):
        return ashlib.util.list_.concatenate([sentence.lemmas for sentence in self.sentences])
    
    def lemmatizedContent(self):
        return " ".join([sentence.lemmatizedContent() for sentence in self.sentences])
    
    def posTags(self):
        return ashlib.util.list_.concatenate([sentence.posTags for sentence in self.sentences])
    
    def nerTags(self):
        return ashlib.util.list_.concatenate([sentence.nerTags for sentence in self.sentences])
    
    def removeSentence(self, index):
        del self.sentences[index]
        for otherIndex in range(index, len(self.sentences)):
            sentence = self.sentences[otherIndex]
            sentence.index = index
    
    def __repr__(self):
        return self.content()  ## TODO: replace with "gloss"

    @classmethod
    def fromFile(cls, filePath):
        return cls(ashlib.util.str_.aggressivelySanitize(ashlib.util.file_.read(filePath)))

## Sentence ######################################################################################

class Sentence(object):
    
    def __init__(self, content, index):
        self.__initialContent = content
        self.index = index
        
        self.words = None
        self.lemmas = None
        self.posTags = None
        self.nerTags = None
    
    def content(self): ## TODO: replace with "gloss"
        return " ".join(self.words)
    
    def numWords(self):
        return len(self.words)
    
    def lemmatizedContent(self):
        return " ".join(self.lemmas)
    
    # Modifications
    
    def parse(self):
        self.words = ashlib.ling.tokenize.words(self.__initialContent)
        words = [word.lower() for word in self.words]
        self.lemmas = ashlib.ling.stem.lemmatize(words)
        self.posTags = ashlib.ling.pos.tag(words)
        self.nerTags = None ## TODO: update later
        
        if VERBOSE: print(("Finished parsing sentence:", self.content()))
    
    def removeWord(self, index):
        del self.words[index]
        del self.lemmas[index]
        del self.posTags[index]
        del self.nerTags[index]
    
    def removeWords(self, indices):
        indices = sorted(indices, reverse=True)
        for index in indices:
            self.removeWord(index)
    
    def replaceWord(self, index, word, lemma=None, posTag=None, nerTag=None):
        self.words[index] = word
        lemma, posTag, nerTag = self.__calculateMetaData(index, word, lemma, posTag, nerTag)
        self.lemmas[index] = lemma
        self.posTags[index] = posTag
        self.nerTags[index] = nerTag
    
    def insertWord(self, index, word, lemma=None, posTag=None, nerTag=None):
        self.words.insert(index, word)
        lemma, posTag, nerTag = self.__calculateMetaData(index, word, lemma, posTag, nerTag)
        self.lemmas.insert(index, lemma)
        self.posTags.insert(index, posTag)
        self.nerTags.insert(index, nerTag)
    
    def insertWords(self, startIndex, words, lemmas=None, posTags=None, nerTags=None):
        for index, word in enumerate(words):
            lemma = None if lemmas is None else lemmas[index]
            posTag = None if posTags is None else posTags[index]
            nerTag = None if nerTags is None else nerTags[index]
            self.insertWord(startIndex + index, word, lemma, posTag, nerTag)
    
    def __calculateMetaData(self, index, word, lemma, posTag, nerTag):
        # it would be too expensive to actually NER tag the whole sentence
        if nerTag is None: nerTag = "O"

        if posTag is None:
            posTags = ashlib.ling.pos.tag(self.words)
            posTag = posTags[index]
        
        if lemma is None:
            # this is expensive - to make it cheaper, pass in just the word as the lemma
            lemma = ashlib.ling.stem.lemmatize(word, self.posTags[index])

        return lemma, posTag, nerTag

    # Default object methods
    
    def __repr__(self):
        return self.content()

    @classmethod
    def concatenate(cls, sentences):
        concatenation = Sentence(content, sentences[0].index)

        concatenation.words = []
        concatenation.lemmas = []
        concatenation.posTags = []
        for sentence in sentences:
            concatenation.words += sentence.words
            concatenation.lemmas += sentence.lemmas
            concatenation.posTags += sentence.posTags
        concatenation.numWords = len(concatenation.words)
        concatenation.lemmatizedContent = " ".join(concatenation.lemmas)

        return concatenation

