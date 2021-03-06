import numpy as np


def get_im2col_indices(x_shape, field_height, field_width, padding=1, stride=1):
  # First figure out what the size of the output should be
  N, C, H, W = x_shape
  assert (H + 2 * padding - field_height) % stride == 0
  assert (W + 2 * padding - field_height) % stride == 0
  out_height = (H + 2 * padding - field_height) / stride + 1
  out_width = (W + 2 * padding - field_width) / stride + 1

  i0 = np.repeat(np.arange(field_height), field_width)
  i0 = np.tile(i0, C)
  i1 = stride * np.repeat(np.arange(out_height), out_width)
  j0 = np.tile(np.arange(field_width), field_height * C)
  j1 = stride * np.tile(np.arange(out_width), out_height)
  i = i0.reshape(-1, 1) + i1.reshape(1, -1)
  j = j0.reshape(-1, 1) + j1.reshape(1, -1)

  k = np.repeat(np.arange(C), field_height * field_width).reshape(-1, 1)

  return (k, i, j)


def im2col_indices(x, field_height, field_width, padding=1, stride=1):
  """ An implementation of im2col based on some fancy indexing """
  # Zero-pad the input
  p = padding
  x_padded = np.pad(x, ((0, 0), (0, 0), (p, p), (p, p)), mode='constant')

  k, i, j = get_im2col_indices(x.shape, field_height, field_width, padding,
                               stride)

  cols = x_padded[:, k, i, j]
  C = x.shape[1]
  cols = cols.transpose(1, 2, 0).reshape(field_height * field_width * C, -1)
  return cols


def col2im_indices(cols, x_shape, field_height=3, field_width=3, padding=1,
                   stride=1):
  """ An implementation of col2im based on fancy indexing and np.add.at """
  N, C, H, W = x_shape
  H_padded, W_padded = H + 2 * padding, W + 2 * padding
  x_padded = np.zeros((N, C, H_padded, W_padded), dtype=cols.dtype)
  k, i, j = get_im2col_indices(x_shape, field_height, field_width, padding,
                               stride)
  cols_reshaped = cols.reshape(C * field_height * field_width, -1, N)
  cols_reshaped = cols_reshaped.transpose(2, 0, 1)
  np.add.at(x_padded, (slice(None), k, i, j), cols_reshaped)
  if padding == 0:
    return x_padded
  return x_padded[:, :, padding:-padding, padding:-padding]


# This is just a copy and paste from the cython version that I did to help debugging
def col2im_slow(cols, N,  C, H, W, k_h, k_w, padding, stride):
    # The // will force the division result to be integer
    HH = (H + 2 * padding - k_h) // stride + 1
    WW = (W + 2 * padding - k_w) // stride + 1
    x_padded = np.zeros((N, C, H + 2 * padding, W + 2 * padding),dtype=cols.dtype)

    # This was a separate function (Again Just to help debugging)
    for c in range(C):
        for ii in range(k_h):
            for jj in range(k_w):
                row = c * k_w * k_h + ii * k_h + jj
                for yy in range(HH):
                    for xx in range(WW):
                        for i in range(N):
                            col = yy * WW * N + xx * N + i
                            x_padded[i, c, stride * yy + ii, stride * xx + jj] += cols[row, col]

    if padding > 0:
        return x_padded[:, :, padding:-padding, padding:-padding]
    return x_padded


def im2col_slow(x, k_h, k_w, padding, stride):
    N = x.shape[0]
    C = x.shape[1]
    H = x.shape[2]
    W = x.shape[3]

    # The // will force the division result to be integer
    HH = (H + 2 * padding - k_h) // stride + 1
    WW = (W + 2 * padding - k_w) // stride + 1

    p = padding
    # Pad image if needed
    x_padded = np.pad(x,((0, 0), (0, 0), (p, p), (p, p)), mode='constant')

    # Allocate output 2d matrix
    cols = np.zeros((C * k_h * k_w, N * HH * WW),dtype=x.dtype)

    # This was a separate function (Again Just to help debugging)
    for c in range(C):
        for yy in range(HH):
            for xx in range(WW):
                for ii in range(k_h):
                    for jj in range(k_w):
                        row = c * k_w * k_h + ii * k_h + jj
                        for i in range(N):
                            col = yy * WW * N + xx * N + i
                            cols[row, col] = x_padded[i, c, stride * yy + ii, stride * xx + jj]

    return cols



pass
