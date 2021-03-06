#!/usr/bin/env python
#-*-coding:utf-8-*-
# @File:utils.py
# @Author: Michael.liu
# @Date:2020/4/23 14:06
# @Desc: 工具类
import numpy as np
from .Relation import *
from .Sentence import *



def cut_sentences(content):
    # 结束符号，包含中文和英文的
    end_flag = ['?', '!', '.', '？', '！', '。', '…']

    content_len = len(content)
    sentences = []
    tmp_char = ''
    for idx, char in enumerate(content):
        # 拼接字符
        tmp_char += char

        # 判断是否已经到了最后一位
        if (idx + 1) == content_len:
            sentences.append(tmp_char)
            break

        # 判断此字符是否为结束符号
        if char in end_flag:
            # 再判断下一个字符是否为结束符号，如果不是结束符号，则切分句子
            next_idx = idx + 1
            if not content[next_idx] in end_flag:
                sentences.append(tmp_char)
                tmp_char = ''

    return sentences

class DataUtil:
     def __init__(self,squence_length):
        self.wordvector_dim = 0
        self.sequence_length =squence_length
        self.word2index = {}
        self.index2vector =[]
        self.relations ={}
        self.bags_train ={}
        self.training_data =[]
        self.bags_test = {}
        self.load_word2vec()
        self.load_relations()

     def load_word2vec(self):
        wordvector =list(open("../data/vector1.txt").readlines())
        wordvector =[s.split() for s in wordvector]
        self.wordvector_dim = len(wordvector[0]) -1
        self.word2index["UNK"] = 0
        self.index2vector.append(np.zeros(self.wordvector_dim))
        index = 1
        for vec in wordvector :
            item  =np.zero(self.wordvector_dim)
            for i in range(self.wordvector_dim):
               item[i] =float(vec[i+1])
            self.word2index[vec[0]] = index
            self.index2vector.append(item)
            index +=1
        print("WordTotal=\t",len(self.index2vector))
        print("Word dimension=\t",self.wordvector_dim)

     def load_relation(self):
        relation_data = list(open("../data/RE/relation2id.txt").readlines())
        relation_data = [s.split() for s in relation_data]
        for relation in relation_data:
            r = Relation(relation[0],int(relation[1]))
            self.relations[relation[0]] = r
        for r in self.relations:
            self.relations[r].generate_vector(len(self.relations))
        print("RelationTotal" + str(len(self.relations)))


     def load_training_data(self,fileName):
        f = open("","a")#open training data
        print("Start loading training data")
        print(">>>>>>>>>>>>>>>")
        training_data =list(open(fileName).readlines())
        training_data = [s.split() for s  in training_data]
        for data in training_data:
            entity1 = data[2]
            entity2 = data[3]
            if data[4] not in self.relations:
                relation = self.relations["NA"]
            else:
                relation = self.relations[data[4]]
            s = Sententce(entity1,entity2,relation,data[5:-1])

            self.training_data.append(s)

            return self.training_data

     def load_testing_data(self):
        print("Start loading testing data")
        print("==================")
        testing_data = list(open("").readlines())
        testing_data = [s.split() for s in testing_data]

        for data in testing_data:
            entity1 = data[2]
            entity2 = data[3]
            if data[4] not in self.relations:
                relation = self.relations["NA"]
            else:
                relation = self.relations[data[4]]
            s = Sententce(entity1,
                         entity2,
                         relation,
                         data[5:-1])
            if data[0] + "\t" + data[1] not in self.bags_test:
                self.bags_test[entity1 + " " + entity2] = [s]
            else:
                self.bags_test[entity1 + " " + entity2].append(s)
        return self.bags_test

     def relation_analyze(self):
        for r in self.relations:
            print(r + ""+ str(self.relations[r].number))


     def batch_iter(self,data,batch_size,num_epochs,shuffle=True):
        data = np.asarray(data)
        data_size = len(data)
        num_batches_per_epoch = int(len(data)/batch_size) + 1
        for epoch in range(num_epochs):
            #Shuffle the data at each epoch
            if shuffle:
                shuffle_indices = np.random.permutation(np.arange(data_size))
                shuffled_data = data[shuffle_indices]
            else:
                shuffled_data = data
            for batch_num in range(num_batches_per_epoch):
                start_index = batch_num * batch_size
                end_index = min((batch_num + 1) * batch_size, data_size)
                if start_index == end_index:
                    continue
                else:
                    yield shuffled_data[start_index:end_index]

     def generate_x(self, data):
         x = []
         for d in data:
             v = []
             words = d.words
             e1 = d.entity1
             e2 = d.entity2
             for i, w in enumerate(words):
                 if w not in self.word2index:
                     tmp = self.index2vector[0]
                 else:
                     tmp = self.index2vector[self.word2index[w]]
                 v.append(tmp)
             vectors = self.padding(v)
             x.append(vectors)
         return x

     def generate_y(self, data):
         return [d.relation.vector for d in data]

     def generate_p(self, data):
         p1 = []
         p2 = []
         for d in data:
             p11 = []
             p22 = []
             e1 = d.entity1
             e2 = d.entity2
             words = d.words
             l1 = 0
             l2 = 0
             for i, w in enumerate(words):
                 if w == e1:
                     l1 = i
                 if w == e2:
                     l2 = i
             for i, w in enumerate(words):
                 a = i - l1
                 b = i - l2
                 if a > 30:
                     a = 30
                 if b > 30:
                     b = 30
                 if a < -30:
                     a = -30
                 if b < -30:
                     b = -30
                 p11.append(a + 31)
                 p22.append(b + 31)
             a = self.sequence_length - len(p11)
             if a > 0:
                 front = a / 2
                 back = a - front
                 front_vec = [0 for i in range(front)]
                 back_vec = [0 for i in range(back)]
                 p11 = front_vec + p11 + back_vec
                 p22 = front_vec + p22 + back_vec
             else:
                 p11 = p11[:self.sequence_length]
                 p22 = p22[:self.sequence_length]
             p1.append(p11)
             p2.append(p22)
         return p1, p2

     def padding(self, vectors):
         a = self.sequence_length - len(vectors)
         if a > 0:
             front = a / 2
             back = a - front
             front_vec = [np.zeros(self.wordvector_dim) for i in range(front)]
             back_vec = [np.zeros(self.wordvector_dim) for i in range(back)]
             vectors = front_vec + vectors + back_vec
         else:
             vectors = vectors[:self.sequence_length]
         return vectors

     def word2num(self, words):
         return [self.words2index[w] for w in words]


