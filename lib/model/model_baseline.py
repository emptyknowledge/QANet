# -*- coding: utf-8 -*-
# Copyright 2019 Huairuo.ai.
# Author: Lin Li (li.lin@huairuo.ai)
#
# cython: language_level=3
#

import torch

from lib.utils import BertConfig, load_bert, mask
from lib.config import Config
from lib.model.model_base import ModelBase
from lib.model.model_utils import DepthwiseSeparableConv, Attention, Encoder, Embedding

class ModelBaseLine(ModelBase):
  """
  The model of baseline.
  """

  def __init__(self, config):
    """

    Args:
      config(Config):
    """
    super(ModelBaseLine, self).__init__(config)
    # self.config = config
    # embedding
    self.embed_word = Embedding(config)

    # encoder
    self.encoder = Encoder(config.encoder_hidden_layer_number,
                           config.bert_config.hidden_size,
                           config.bert_config.max_position_embeddings,
                           config.encoder_intermediate_dim,
                           config.attention_head_num,
                           config.attention_droup_out,
                           config.attention_use_bias)

    # pointer
    self.pointer_linear = torch.nn.Linear(config.bert_config.hidden_size, 2)
    # self.pointer_softmax = torch.nn.Softmax(dim=-2)



  def pointer(self, embeddings, input_mask):
    """"""
    # size: batch_size, seq_length, 2
    embeddings = self.pointer_linear(embeddings)
    embeddings = mask(embeddings, input_mask, -2)
    start_embeddings = embeddings[:, :, 0].squeeze(dim=-1)
    end_embeddings = embeddings[:, :, 1].squeeze(dim=-1)
    return start_embeddings, end_embeddings

    # embeddings = self.pointer_softmax(embeddings)
    # start_softmax = embeddings[:,:,0]
    # end_softmax = embeddings[:,:,1]
    # start, end, pro = find_max_proper_batch(start_softmax, end_softmax)
    # return start, end, pro

  def forward(self, input_ids, input_mask, segment_ids,
              question_ids=None, question_mask=None, question_segment_ids=None):
    """

    Args:
      input_ids:
      input_mask:
      segment_ids:
      question_ids(): 默认 None， None： 表示 question token 与 context token
        都在 input_ids 中，否则 input_ids 只有 context token。
      question_mask:
      question_segment_ids:

    Returns:

    """
    embedding = self.embed_word(input_ids, segment_ids)
    value_embedding = (self.embed_word(question_ids, question_segment_ids)
                        if question_ids else embedding)
    embedding = self.encoder(embedding, value_embedding, input_mask)
    start, end = self.pointer(embedding, input_mask)
    return start, end


class ModelBaselineSQC(ModelBase):
  """
  Model baseline, question tokens 和 context tokens 是分开的。
  """
  def __init__(self, config):
    """"""
    super(ModelBaselineSQC, self).__init__(config)
    self.embedding = Embedding(config)

    self.pointor = torch.nn.Linear(config.bert_config.hidden_size, 2)