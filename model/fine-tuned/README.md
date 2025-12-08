---
library_name: peft
license: other
base_model: DeepSeek-R1-Distill-Llama-8B
tags:
- llama-factory
- lora
- generated_from_trainer
model-index:
- name: '0415'
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# 0415

This model is a fine-tuned version of [DeepSeek-R1-Distill-Llama-8B](https://huggingface.co/DeepSeek-R1-Distill-Llama-8B) on the code_train dataset.
It achieves the following results on the evaluation set:
- Loss: 0.0934

## Model description

More information needed

## Intended uses & limitations

More information needed

## Training and evaluation data

More information needed

## Training procedure

### Training hyperparameters

The following hyperparameters were used during training:
- learning_rate: 0.0002
- train_batch_size: 1
- eval_batch_size: 1
- seed: 42
- optimizer: Use OptimizerNames.ADAMW_TORCH with betas=(0.9,0.999) and epsilon=1e-08 and optimizer_args=No additional optimizer arguments
- lr_scheduler_type: cosine
- lr_scheduler_warmup_ratio: 0.1
- num_epochs: 3.0

### Training results

| Training Loss | Epoch  | Step | Validation Loss |
|:-------------:|:------:|:----:|:---------------:|
| 0.426         | 2.3923 | 1000 | 0.2576          |


### Framework versions

- PEFT 0.12.0
- Transformers 4.48.2
- Pytorch 2.5.1+cu124
- Datasets 3.2.0
- Tokenizers 0.21.0