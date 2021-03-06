'''This script demonstrates how to build a variational autoencoder
with Keras and deconvolution layers.

# Reference

- Auto-Encoding Variational Bayes
  https://arxiv.org/abs/1312.6114
'''
from __future__ import print_function

import numpy as np
from scipy.stats import norm
from PIL import Image

from keras.layers import Input, Dense, Lambda, Flatten, Reshape
from keras.layers import Conv2D, Conv2DTranspose, MaxPooling2D, UpSampling2D
from keras.models import Model
from keras import backend as K
from keras import metrics
from keras.datasets import cifar10

# output path
fpath = '/home/yliu0/data/cifar/'

# input image dimensions
img_rows, img_cols, img_chns = 32, 32, 3
# number of convolutional filters to use
filters = 64
# convolution kernel size
num_conv = 3

epochs = 30   # converges at around 10th epoch, loss = 651
batch_size = 100
if K.image_data_format() == 'channels_first':
    original_img_size = (img_chns, img_rows, img_cols)
else:
    original_img_size = (img_rows, img_cols, img_chns)
latent_dim = 2
intermediate_dim = 128
epsilon_std = 1.0

x = Input(shape=original_img_size)
l = Conv2D(img_chns, kernel_size=(2, 2), padding='same', activation='relu')(x)
l = Conv2D(filters, kernel_size=(2, 2), padding='same', activation='relu',
                strides=(2, 2))(l)
l = Conv2D(filters, kernel_size=num_conv, padding='same', activation='relu',
                strides=1)(l)
l = MaxPooling2D((2, 2), padding='same')(l)
l = Conv2D(filters, kernel_size=num_conv, padding='same', activation='relu',
                strides=1)(l)
l = MaxPooling2D((2, 2), padding='same')(l)
# at this point the output shape is (4, 4, filters)
flat = Flatten()(l)
hidden = Dense(intermediate_dim, activation='relu')(flat)

z_mean = Dense(latent_dim)(hidden)
z_log_var = Dense(latent_dim)(hidden)


def sampling(args):
    z_mean, z_log_var = args
    epsilon = K.random_normal(shape=(K.shape(z_mean)[0], latent_dim),
                              mean=0., stddev=epsilon_std)
    return z_mean + K.exp(z_log_var) * epsilon

# note that "output_shape" isn't necessary with the TensorFlow backend
# so you could write `Lambda(sampling)([z_mean, z_log_var])`
z = Lambda(sampling, output_shape=(latent_dim,))([z_mean, z_log_var])

# we instantiate these layers separately so as to reuse them later
decoder_hid = Dense(intermediate_dim, activation='relu')
decoder_upsample = Dense(filters * 4 * 4, activation='relu')

if K.image_data_format() == 'channels_first':
    output_shape = (batch_size, filters, 4, 4)
else:
    output_shape = (batch_size, 4, 4, filters)

decoder_reshape = Reshape(output_shape[1:])
decoder_deconv_1 = Conv2DTranspose(filters,
                                   kernel_size=num_conv,
                                   padding='same',
                                   strides=1,
                                   activation='relu')
decoder_unpool = UpSampling2D((2, 2))
decoder_deconv_2 = Conv2DTranspose(filters,
                                   kernel_size=num_conv,
                                   padding='same',
                                   strides=1,
                                   activation='relu')
decoder_deconv_3_upsamp = Conv2DTranspose(filters,
                                          kernel_size=(3, 3),
                                          strides=(2, 2),
                                          padding='valid',
                                          activation='relu')
decoder_mean_squash = Conv2D(img_chns,
                             kernel_size=2,
                             padding='valid',
                             activation='sigmoid')

l = decoder_hid(z)
l = decoder_upsample(l)
l = decoder_reshape(l)
l = decoder_deconv_1(l)
l = decoder_unpool(l)
l = decoder_deconv_2(l)
l = decoder_unpool(l)
l = decoder_deconv_3_upsamp(l)
x_decoded_mean_squash = decoder_mean_squash(l)

# instantiate VAE model
vae = Model(x, x_decoded_mean_squash)

# Compute VAE loss
xent_loss = img_rows * img_cols * metrics.binary_crossentropy(
    K.flatten(x),
    K.flatten(x_decoded_mean_squash))
kl_loss = - 0.5 * K.sum(1 + z_log_var - K.square(z_mean) - K.exp(z_log_var), axis=-1)
vae_loss = K.mean(xent_loss + kl_loss)
vae.add_loss(vae_loss)

vae.compile(optimizer='rmsprop')
vae.summary()

# train the VAE on CIFAR 10 images
(x_train, _), (x_test, y_test) = cifar10.load_data()

x_train = x_train.astype('float32') / 255.
x_train = x_train.reshape((x_train.shape[0],) + original_img_size)
x_test = x_test.astype('float32') / 255.
x_test = x_test.reshape((x_test.shape[0],) + original_img_size)

print('x_train.shape:', x_train.shape)

vae.fit(x_train,
        shuffle=True,
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(x_test, None))

# build a model to project inputs on the latent space
encoder = Model(x, z_mean)

# build a digit generator that can sample from the learned distribution
decoder_input = Input(shape=(latent_dim,))
l = decoder_hid(decoder_input)
l = decoder_upsample(l)
l = decoder_reshape(l)
l = decoder_deconv_1(l)
l = decoder_unpool(l)
l = decoder_deconv_2(l)
l = decoder_unpool(l)
l = decoder_deconv_3_upsamp(l)
_x_decoded_mean_squash = decoder_mean_squash(l)
generator = Model(decoder_input, _x_decoded_mean_squash)

# encode and decode
x_test_encoded = encoder.predict(x_test, batch_size=batch_size)
x_test_decoded = generator.predict(x_test_encoded)

m = 5
original = np.zeros((img_rows * m, img_cols * m, img_chns), 'uint8')
reconstructed = np.zeros((img_rows * m, img_cols * m, img_chns), 'uint8')

def to_image (array):
    array = array.reshape(img_rows, img_cols, img_chns)
    array *= 255
    return array.astype('uint8')

for i in range(m):
    for j in range(m):
        k = i * m + j
        orig = to_image(x_test[k])
        re = to_image(x_test_decoded[k])
        original[i * img_rows: (i + 1) * img_rows,
               j * img_cols: (j + 1) * img_cols] = orig
        reconstructed[i * img_rows: (i + 1) * img_rows,
               j * img_cols: (j + 1) * img_cols] = re

img = Image.fromarray(original, 'RGB')
img.save(fpath + 'original.png')
img = Image.fromarray(reconstructed, 'RGB')
img.save(fpath + 'reconstructed.png')
