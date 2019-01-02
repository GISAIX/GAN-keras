import beefly
import numpy as np
import tensorflow as tf


def generator(latent_dim=100, num_classes=10, image_shape=(28,28,1)):
    noise = tf.keras.Input(shape=(latent_dim,))
    x = tf.keras.layers.Dense(256)(noise)
    x = tf.keras.layers.LeakyReLU(alpha=0.2)(x)
    x = tf.keras.layers.BatchNormalization(momentum=0.8)(x)
    x = tf.keras.layers.Dense(512)(x)
    x = tf.keras.layers.LeakyReLU(alpha=0.2)(x)
    x = tf.keras.layers.BatchNormalization(momentum=0.8)(x)
    x = tf.keras.layers.Dense(1024)(x)
    x = tf.keras.layers.LeakyReLU(alpha=0.2)(x)
    x = tf.keras.layers.BatchNormalization(momentum=0.8)(x)
    x = tf.keras.layers.Dense(np.prod(image_shape), activation='tanh')(x)
    image = tf.keras.layers.Reshape(image_shape)(x)
    gnet = tf.keras.Model(noise, image)
    return gnet

def discriminator(image_shape=(28,28,1), num_classes=10):
    image = tf.keras.Input(shape=image_shape)
    x = tf.keras.layers.Flatten()(image)
    x = tf.keras.layers.Dense(512)(x)
    x = tf.keras.layers.LeakyReLU(alpha=0.2)(x)
    x = tf.keras.layers.Dense(256)(x)
    x = tf.keras.layers.LeakyReLU(alpha=0.2)(x)
    logit = tf.keras.layers.Dense(1)(x)
    dnet = tf.keras.Model(image, logit)
    return dnet

def train(batch_num=10000, batch_size=64, latent_dim=100, image_shape=(28,28,1)):
    tf.logging.set_verbosity(tf.logging.ERROR)
    dnet = discriminator(image_shape)
    dnet.compile(loss=['mse'], 
                 optimizer=tf.keras.optimizers.Adam(0.0002, 0.5),
                 metrics=['accuracy'])

    noise = tf.keras.Input(shape=(latent_dim,))
    gnet = generator(latent_dim, image_shape)
    dnet.trainable = False
    image = gnet(noise)
    logit = dnet(image)
    lsgan = tf.keras.Model(noise, logit)
    lsgan.compile(loss=['mse'],
                  optimizer=tf.keras.optimizers.Adam(0.0002, 0.5),
                  metrics=['accuracy'])
    
    (X_train, _), (_, _) = tf.keras.datasets.fashion_mnist.load_data()
    X_train = X_train / 127.5 - 1.
    X_train = np.expand_dims(X_train, axis=3)
    
    beeplot = beefly.plot_metrics(columns=2, wait_num=50)
    for batch in range(batch_num):
        batch_image = X_train[np.random.choice(range(X_train.shape[0]), batch_size, False)]
        batch_noise = np.random.normal(0, 1, (batch_size, latent_dim))
        batch_gen_image = gnet.predict(batch_noise)

        d_loss_real = dnet.train_on_batch(batch_image, np.ones((batch_size, 1)))
        d_loss_fake = dnet.train_on_batch(batch_gen_image, np.zeros((batch_size, 1)))
        d_loss = 0.5 * np.add(d_loss_real, d_loss_fake)
        g_loss = lsgan.train_on_batch(batch_noise, np.ones((batch_size, 1)))
        if batch%1==0:
            beeplot.update({'D_loss': d_loss[0], 'D_binary_acc': d_loss[1],
                            'G_loss': g_loss[0], 'G_binary_acc': g_loss[1]})
            beeplot.draw()
    return gnet


if __name__ == '__main__':
    gnet = train()
