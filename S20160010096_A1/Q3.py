# -*- coding: utf-8 -*-
"""dl_a1_q3_rnn_v1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1SC03cKwC-6kjkOTbwnJmD9AFHWTCQI6F
"""

"""
    RNN

    Name - Tanmay Kalani
    Roll No. - S20160010096
"""

import pandas as pd
import tensorflow as tf
import numpy as np
import string, collections, sklearn.utils, math
import matplotlib.pyplot as plt
import matplotlib

def convert_to_one_hot(Y, C):
    """
        Convert to one-hot-encoding
    """
    res = np.eye(C)[np.array(Y).reshape(-1)]
    return res.reshape(list(Y.shape)+[C])

def load_dataset():
    """
        Load Dataset
    """
    data = pd.read_csv('mrdata.tsv', sep='\t')                                          # Reading data
    data.columns =['PhraseId', 'SentenceId', 'Phrase', 'Sentiment']
    data = sklearn.utils.shuffle(data)                                                  # Shuffle Data
    print("Data Shape : {}".format(data.shape))
    return data

def train_test_split(sentiment_data):
    """
        Split train and test dataset
    """
    train_data = np.array(sentiment_data[:])[:, [2, 3]]
    test_data = np.array(sentiment_data[124848:])[:, [2]]
    return  train_data, test_data

def split_to_reviews_and_labels(final_train_data, final_test_data):
    """
        Split to LABEL and REVIEWS

        test_ratio = 0.2
    """
    labels, reviews = final_train_data[:, [1]], final_train_data[:, [0]]
    unlabeled_reviews = final_test_data

    print("Train Shape : {}".format(labels.shape))
    print("Reviews Shape : {}".format(reviews.shape))
    print("Test Shape : {}".format(unlabeled_reviews.shape))

    reviews_processed, unlabeled_reviews_processed = [], []
    reviews_processed.extend([''.join([char for char in review if char not in string.punctuation]) for review in reviews])
    unlabeled_reviews_processed.extend([''.join([char for char in review if char not in string.punctuation]) for review in unlabeled_reviews])

    word_reviews, word_unlabeled, all_words = [], [], []
    for review in reviews_processed:
        word_reviews.append(review.lower().split())
        all_words.extend([each_word.lower() for each_word in review.split()])

    for review in unlabeled_reviews_processed:
        word_unlabeled.append(review.lower().split())
        all_words.extend([each_word.lower() for each_word in review.split()])
        
    counter = collections.Counter(all_words)
    vocab = sorted(counter, key=counter.get, reverse=True)
    vocabulary_to_int_dict = {word: i for i, word in enumerate(vocab, 1)}               # Converting vocabulary to integer dictionary
    len_sequence = 52

    reviews_to_int_dict = []
    reviews_to_int_dict.extend([[vocabulary_to_int_dict[word] for word in review] for review in word_reviews])
    features = np.zeros((len(reviews_to_int_dict), len_sequence), dtype=int)
    for i, review in enumerate(reviews_to_int_dict):
        if(len(review)):
            features[i, -len(review):] = np.array(review)[:len_sequence]

    reviews_lens = collections.Counter([len(x) for x in reviews_to_int_dict])

    unlabeled_to_int_dict = []
    unlabeled_to_int_dict.extend([[vocabulary_to_int_dict[word] for word in review] for review in word_unlabeled])
    test_features = np.zeros((len(unlabeled_to_int_dict), len_sequence), dtype=int)
    for i, review in enumerate(unlabeled_to_int_dict):
        if(len(review)):
            test_features[i, -len(review):] = np.array(review)[:len_sequence]

    print("Features Shape : {}".format(features.shape))
    print("Test Features Shape : {}".format(test_features.shape))

    X_train = features[:124900]                                             # Dividing features to train and test
    y_train = labels[:124900]                                               # Dividing labels to train and test

    X_test = features[124900:]                                              # Dividing features to train and test
    y_test = labels[124900:]                                                # Dividing labels to train and test

    X_unlabeled = test_features

    print('X_train shape {}'.format(X_train.shape))
    print('X_unlabeled shape {}'.format(X_unlabeled.shape))

    return X_train, y_train, X_test, y_test, vocabulary_to_int_dict

def create_placeholders():
    """
        Creates tensorflow placeholders

        Return:
        inputs = placeholder for inputs
        outputs = placeholder for output label
    """
    inputs = tf.placeholder(tf.int32, [None, None], name='inputs')          # Create placeholders for input
    targets = tf.placeholder(tf.int32, [None, None], name='targets')        # Create placeholders for output
    return inputs, targets

def initialize_parameters(number_of_words, embed_size, inputs):
    """
        Initializing RNN parameters

        Args:
            number_of_words
            embed_size - Embedding Size
            input - Input
        
        Returns:
            Tensors of word embeddings
    """
    word_embeddings = tf.Variable(tf.random_uniform((number_of_words, embed_size), -1, 1))
    embed = tf.nn.embedding_lookup(word_embeddings, inputs)                  # Create Word Embeddings
    return word_embeddings, embed

def forward_propagation(hidden_layer_size, dropout_rate, number_of_layers, embed, batch_size):
    """
        Implements the forward propagation for the model:
        
        Arguments:
            hidden_layer_size - Size of hidden layer
            dropout_rate - Dropout rate
            number_of_layers - number of layers
            embed - Embeddings
            batch_size - Batch Size

        Returns:
            outputs, states - Dynamic RNN Cell
    """
    hidden_layer = tf.contrib.rnn.BasicLSTMCell(hidden_layer_size)                  # Create LSTM Cell
    hidden_layer = tf.contrib.rnn.DropoutWrapper(hidden_layer, dropout_rate)        # Dropout

    cell = tf.contrib.rnn.MultiRNNCell([hidden_layer]*number_of_layers)             # RNN Cell
    init_state = cell.zero_state(batch_size, tf.float32)

    outputs, states = tf.nn.dynamic_rnn(cell, embed, initial_state=init_state)      # Dynamic RNN
    return outputs, states

def compute_cost(outputs, targets):
    """
        Computes Cost

        Args:
            outputs -- output of RNN
            targets -- expected output from dataset

        Returns:
            cost
    """
    prediction = tf.layers.dense(outputs[:, -1], 5)                                 # Dense Layer
    cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(labels=targets, logits=prediction))    # Claculate Softmax
    return prediction, cost

def model(X_train, Y_train, X_test, Y_test, vocabulary_to_int_dict,
        learning_rate = 0.009, num_epochs = 100, batch_size = 32, hidden_layer_size=128, number_of_layers=1, dropout_rate=0.8, embed_size=10, epochs=10, seed=3):

    number_of_words = len(vocabulary_to_int_dict) + 1

    tf.reset_default_graph()
    inputs, targets = create_placeholders()
    word_embeddings, embed = initialize_parameters(number_of_words, embed_size, inputs)
    outputs, states = forward_propagation(hidden_layer_size, dropout_rate, number_of_layers, embed, batch_size)
    prediction, cost = compute_cost(outputs, targets)

    optimizer = tf.train.AdamOptimizer(learning_rate).minimize(cost)

    currect_pred = tf.equal(tf.argmax(tf.nn.softmax(prediction),1), tf.argmax(targets,1))
    accuracy = tf.reduce_mean(tf.cast(currect_pred, tf.float32))

    with tf.Session() as session:
        session.run(tf.global_variables_initializer())

        costs = []
        for epoch in range(epochs):

            count, last_index = 0, 0
            training_accurcy, epoch_loss = [], []
            
            while last_index + batch_size <= len(X_train) and count<500:
                minibatch_X = X_train[last_index:last_index+batch_size]
                minibatch_Y = Y_train[last_index:last_index+batch_size].reshape(-1, 1)
                minibatch_Y = convert_to_one_hot(minibatch_Y.astype(np.int32),5).reshape((batch_size,5))
                
                acc, loss, _ = session.run([accuracy, cost, optimizer], feed_dict={inputs:minibatch_X, targets:minibatch_Y})
                
                training_accurcy.append(acc)
                epoch_loss.append(loss)
                count += 1
                last_index += batch_size
            # print('Epoch: {}/{}'.format(i, epochs), ' | Current loss: {}'.format(np.mean(epoch_loss)), ' | Training accuracy: {:.4f}%'.format(np.mean(training_accurcy)*100))
            print ("Cost after epoch {}: {}".format(epoch, np.mean(epoch_loss)))
            costs.append(np.mean(epoch_loss))

        test_accuracy = []
        count, last_index = 0, 0
        while last_index + batch_size <= len(X_test):
            minibatch_X = X_test[last_index:last_index+batch_size]
            minibatch_Y = y_test[last_index:last_index+batch_size].reshape(-1, 1)

            acc = session.run([accuracy], feed_dict={inputs:minibatch_X, targets:minibatch_Y})
            
            test_accuracy.append(acc)
            last_index += batch_size
            count += 1
        
        print("Test accuracy is {}%".format(np.mean(test_accuracy)*100))

        plt.plot(np.squeeze(costs))
        plt.ylabel('cost')
        plt.xlabel('iterations')
        plt.title("Learning rate =" + str(learning_rate))
        plt.show()

if __name__ == '__main__':
    sentiment_data = load_dataset()
    final_train_data, final_test_data = train_test_split(sentiment_data)
    X_train, y_train, X_test, y_test, vocabulary_to_int_dict = split_to_reviews_and_labels(final_train_data, final_test_data)
    model(X_train, y_train, X_test, y_test, vocabulary_to_int_dict)