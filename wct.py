import numpy as np
from utils import save_img
from numpy.lib.scimath import sqrt as csqrt
import tensorflow as tf

def wct_test(encodings, alpha):
    return tf.identity(encodings)


def wct_tf(content, style, alpha, eps=1e-5):
    '''TF version of Whiten-Color Transform
        Assume that 1) content/style encodings are stacked in first two rows
        and 2) they have shape format HxWxC
    '''
    # Remove batch dim and reorder to CxHxW
    content_t = tf.transpose(tf.squeeze(content), (2, 0, 1))
    style_t = tf.transpose(tf.squeeze(style), (2, 0, 1))

    C, H, W = tf.unstack(tf.shape(content_t))
    _, Hs, Ws = tf.unstack(tf.shape(style_t))

    # CxHxW -> CxH*W
    content_flat = tf.reshape(content_t, (C, H*W))
    style_flat = tf.reshape(style_t, (C, Hs*Ws))

    # Center content
    mc = tf.reduce_mean(content_flat, axis=1, keep_dims=True)
    fc = content_flat - mc

    fcfc = tf.matmul(fc, fc, transpose_b=True)
    
    Sc, Uc, Vc = tf.svd(fcfc, full_matrices=True)

    Dc_sq_inv = tf.diag(tf.pow(Sc+eps, -0.5))

    fc_hat = tf.matmul(tf.matmul(tf.matmul(Uc, Dc_sq_inv), tf.transpose(Uc)), fc)

    # Compute style coloring
    ms = tf.reduce_mean(style_flat, axis=1, keep_dims=True)
    fs = style_flat - ms

    fsfs = tf.matmul(fs, tf.transpose(fs))

    Ss, Us, Vs = tf.svd(fsfs, full_matrices=True)
    
    Ds_sq = tf.diag(tf.pow(Ss+eps, 0.5))

    fcs_hat = tf.matmul(tf.matmul(tf.matmul(Us, Ds_sq), tf.transpose(Us)), fc_hat)

    fcs_hat = fcs_hat + ms

    blended = alpha*fcs_hat + (1 - alpha)*(fc)

    # CxH*W -> CxHxW
    blended = tf.reshape(blended, (C,H,W))
    # CxHxW -> NxHxWxC
    blended = tf.expand_dims(tf.transpose(blended, (1,2,0)), 0)

    return blended
     

def wct(content, style, alpha=0.6, eps=1e-5):
    '''Perform Whiten-Color Transform on feature maps
       See p.4 of the Universal Style Transfer paper for equations:
       https://arxiv.org/pdf/1705.08086.pdf
    '''    
    # HxWxC -> CxHxW
    content_t = np.transpose(content, (2, 0, 1))
    style_t = np.transpose(style, (2, 0, 1))

    # CxHxW -> CxH*W
    content_flat = content_t.reshape(-1, content_t.shape[1]*content_t.shape[2])
    style_flat = style_t.reshape(-1, style_t.shape[1]*style_t.shape[2])

    # Center content
    mc = content_flat.mean(axis=1, keepdims=True)
    fc = content_flat - mc

    fcfc = np.dot(fc, fc.T)
    
    Ec, wc, _ = np.linalg.svd(fcfc)

    Dc_sq_inv = np.linalg.inv(np.sqrt(np.diag(wc_eps)))

    fc_hat = Ec.dot(Dc_sq_inv).dot(Ec.T).dot(fc)

    # Compute style coloring
    ms = style_flat.mean(axis=1, keepdims=True)
    fs = style_flat - ms

    fsfs = np.dot(fs, fs.T)

    Es, ws, _ = np.linalg.svd(fsfs)
    
    Ds_sq = np.sqrt(np.diag(ws+eps))

    fcs_hat = Es.dot(Ds_sq).dot(Es.T).dot(fc_hat)

    fcs_hat = fcs_hat + ms

    blended = alpha*fcs_hat + (1 - alpha)*(fc)

    # CxH*W -> CxHxW
    blended = blended.reshape(content_t.shape)

    # CxHxW -> HxWxC
    blended = np.transpose(blended, (1,2,0))  
    
    return blended