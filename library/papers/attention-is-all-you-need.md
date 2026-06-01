---
type: source
title: "Attention Is All You Need"
status: active
authors: [Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin]
venue: "NeurIPS 2017"
year: 2017
url: https://arxiv.org/abs/1706.03762
tags: [paper, ai, transformers, attention, nlp]
---

# Attention Is All You Need - Detailed Memex Summary

## One-sentence summary

Vaswani et al. introduce the **Transformer**, an encoder-decoder neural architecture for sequence transduction that replaces recurrent and convolutional layers with **multi-head self-attention**, achieving state-of-the-art machine translation quality while training much faster through parallel computation.

## Core thesis

The paper argues that recurrent neural networks and convolutional sequence models impose unnecessary computational structure on sequence modeling. RNNs process tokens sequentially, which limits parallelism. Convolutional models parallelize better but need multiple layers or dilation to connect distant positions. The Transformer removes recurrence and convolution entirely and uses attention as the main operation for representing dependencies between tokens.

The key claim is not merely that attention helps sequence modeling. Earlier encoder-decoder models already used attention. The claim is stronger: **attention alone is sufficient as the core mechanism for high-performing sequence transduction**, provided it is organized with multi-head projections, positional encodings, residual connections, layer normalization, feed-forward sublayers, and masking in the decoder.

## Paper metadata

| Field | Value |
|---|---|
| Title | *Attention Is All You Need* |
| Authors | Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin |
| Venue | NIPS 2017, Long Beach, CA, USA |
| Main artifact | Transformer architecture |
| Primary tasks evaluated | WMT 2014 English-to-German and English-to-French machine translation |
| Main reported metric | BLEU |
| Central technical mechanism | Scaled dot-product attention and multi-head attention |
| Main architectural departure | No recurrence and no convolution in the encoder or decoder |

## Authors / writers and stated contributions

The paper marks every listed author with equal contribution and says that the listing order is random. The contribution footnote is unusually detailed; it distributes credit across idea origination, first implementation, attention mechanisms, model variants, codebases, inference, visualization, and Tensor2Tensor infrastructure.

| Author | Affiliation in paper | Stated contribution in the paper |
|---|---|---|
| **Ashish Vaswani** | Google Brain | With Illia Polosukhin, designed and implemented the first Transformer models; involved across the work. |
| **Noam Shazeer** | Google Brain | Proposed scaled dot-product attention, multi-head attention, and the parameter-free position representation; involved across many details. |
| **Niki Parmar** | Google Research | Designed, implemented, tuned, and evaluated many model variants in the original codebase and Tensor2Tensor. |
| **Jakob Uszkoreit** | Google Research | Proposed replacing RNNs with self-attention and initiated the effort to evaluate the idea. |
| **Llion Jones** | Google Research | Experimented with model variants; responsible for the initial codebase, efficient inference, and visualizations. |
| **Aidan N. Gomez** | University of Toronto; work performed while at Google Brain | Helped design and implement Tensor2Tensor, replacing the earlier codebase and accelerating research. |
| **Łukasz Kaiser** | Google Brain | Helped design and implement Tensor2Tensor, replacing the earlier codebase and accelerating research. |
| **Illia Polosukhin** | Work performed while at Google Research | With Ashish Vaswani, designed and implemented the first Transformer models. |

### Interpretation of the authorship structure

The authorship note suggests the paper emerged from a collaborative engineering-research process rather than a single isolated theoretical insight. Jakob Uszkoreit is credited with the initial conceptual push away from RNNs toward self-attention. Ashish Vaswani and Illia Polosukhin are credited with first-model design and implementation. Noam Shazeer contributed several of the core mechanisms that became canonical: scaled dot-product attention, multi-head attention, and a parameter-free positional representation. Niki Parmar and Llion Jones drove extensive experimentation and implementation work. Łukasz Kaiser and Aidan Gomez helped move the work onto Tensor2Tensor, improving reproducibility, speed, and research iteration.

For a memex, it is useful to store this as: **Transformer = architecture + mechanism + systems work + ablation-driven tuning**.

## Why the paper was written

Before this paper, dominant sequence transduction systems typically used recurrent neural networks, especially LSTMs and GRUs, inside encoder-decoder architectures. Attention mechanisms were already widely used, but usually as a supplement to recurrence rather than as a replacement for it.

The authors identify a bottleneck: RNNs process sequence positions step by step. This creates an inherently sequential computation graph. During training, that sequential dependency prevents full parallelization within a single example. The bottleneck becomes worse for long sequences because memory constraints limit how much batching can compensate.

Convolutional sequence models address some of this by computing hidden representations in parallel over positions, but convolutions require either deeper stacks or dilated structures to allow distant positions to interact. In such models, the path length between two arbitrary positions grows with their distance or with the number of layers needed to bridge them.

The Transformer is presented as an answer to both problems: it lets all positions interact through attention in a constant number of sequential operations while retaining efficient matrix-multiplication implementation.

## Main contribution

The paper's main contribution is the **Transformer**, described as the first sequence transduction architecture based entirely on attention, without sequence-aligned recurrence or convolution.

The architecture combines several elements:

1. **Encoder-decoder structure** for sequence-to-sequence modeling.
2. **Stacked self-attention layers** in both encoder and decoder.
3. **Multi-head attention** to let the model attend across multiple representation subspaces.
4. **Scaled dot-product attention** to stabilize dot-product attention at larger key/query dimensions.
5. **Masked decoder self-attention** to preserve autoregressive generation.
6. **Position-wise feed-forward networks** after attention sublayers.
7. **Residual connections and layer normalization** around sublayers.
8. **Sinusoidal positional encodings** to represent token order despite the absence of recurrence and convolution.
9. **Weight sharing** between embeddings and the pre-softmax linear transformation.

## Architecture overview

The Transformer preserves the broad encoder-decoder shape used in earlier sequence-to-sequence systems, but changes the internal computation.

### Encoder

The encoder maps an input sequence into a sequence of continuous representations. It consists of **N = 6 identical layers** in the base model.

Each encoder layer has two sublayers:

1. **Multi-head self-attention**: every position in the input can attend to every other input position.
2. **Position-wise feed-forward network**: the same feed-forward transformation is applied independently to each sequence position.

Each sublayer is wrapped in a residual connection followed by layer normalization:

```text
LayerNorm(x + Sublayer(x))
```

The base model uses `d_model = 512` for embeddings and all sublayer outputs, which allows residual connections to add tensors with compatible dimensions.

### Decoder

The decoder also uses **N = 6 identical layers**, but each decoder layer has three sublayers:

1. **Masked multi-head self-attention** over previously generated output positions.
2. **Encoder-decoder multi-head attention**, where decoder states provide queries and encoder outputs provide keys and values.
3. **Position-wise feed-forward network**.

The mask prevents a decoder position from attending to future positions. This preserves the autoregressive property: the prediction for output token `i` can only depend on known outputs before `i`.

### Figure 1: Transformer architecture diagram

The architecture diagram on page 3 shows the encoder stack on the left and decoder stack on the right. Both stacks begin with token embeddings plus positional encodings. The encoder repeats a multi-head attention block followed by a feed-forward block. The decoder repeats masked multi-head attention, encoder-decoder attention, and feed-forward blocks. The top of the decoder passes through a linear projection and softmax to produce output probabilities.

The figure is important because it shows that the Transformer is not just "attention" in isolation. It is a modular residual architecture built from attention, feed-forward layers, normalization, embeddings, positional encodings, and output projection.

## Attention mechanism

### Scaled dot-product attention

The paper defines attention as mapping queries, keys, and values to outputs. A query is compared to keys; the resulting compatibility scores become weights over values.

The Transformer uses scaled dot-product attention:

```text
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
```

Where:

- `Q` is the query matrix.
- `K` is the key matrix.
- `V` is the value matrix.
- `d_k` is the dimensionality of keys and queries.

The scaling factor `1 / sqrt(d_k)` matters because raw dot products grow in magnitude as dimensionality increases. Large dot products can push softmax into regions with very small gradients. Scaling keeps the logits numerically better behaved.

### Multi-head attention

Instead of running a single attention operation over the full model dimension, the Transformer projects queries, keys, and values into multiple smaller subspaces and performs attention in parallel. The outputs of the heads are concatenated and projected again.

In simplified form:

```text
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O
head_i = Attention(Q W_i^Q, K W_i^K, V W_i^V)
```

In the base model:

- `h = 8` attention heads.
- `d_model = 512`.
- `d_k = d_v = 64` per head.

Multi-head attention allows the model to represent different kinds of relationships at different positions and representation subspaces. A single attention head would tend to average over all relevant positions in one space; multiple heads let the model separate concerns.

### Three uses of attention in the model

The Transformer uses attention in three places:

| Attention type | Location | Queries | Keys and values | Purpose |
|---|---|---|---|---|
| Encoder self-attention | Encoder | Encoder states | Encoder states | Let each input token attend to all input tokens. |
| Decoder masked self-attention | Decoder | Decoder states | Decoder states up to current position | Let each output token use previous output context without seeing the future. |
| Encoder-decoder attention | Decoder | Decoder states | Encoder outputs | Let each output position attend to the full input sequence. |

## Feed-forward networks

Each encoder and decoder layer includes a position-wise feed-forward network. It is applied independently and identically to each position:

```text
FFN(x) = max(0, xW_1 + b_1)W_2 + b_2
```

The base model uses:

- Input/output dimensionality: `d_model = 512`.
- Inner hidden dimensionality: `d_ff = 2048`.
- Activation: ReLU.

The paper notes this can be interpreted as two kernel-size-1 convolutions, but the important point is that this part mixes features within a position, while attention mixes information across positions.

## Embeddings, softmax, and weight sharing

The Transformer uses learned token embeddings for input and output tokens. It also uses a learned linear transformation plus softmax to convert decoder outputs into next-token probabilities.

The paper shares the same weight matrix between:

1. Input token embedding.
2. Output token embedding.
3. Pre-softmax linear transformation.

Embedding weights are multiplied by `sqrt(d_model)`, a scaling convention used to match magnitudes in the architecture.

## Positional encodings

Because the Transformer has no recurrence or convolution, token order is not built into the architecture. The model needs explicit positional information.

The paper adds positional encodings to token embeddings at the bottoms of the encoder and decoder stacks. The chosen default is sinusoidal:

```text
PE(pos, 2i)     = sin(pos / 10000^(2i / d_model))
PE(pos, 2i + 1) = cos(pos / 10000^(2i / d_model))
```

Where:

- `pos` is the token position.
- `i` is the dimension index.
- Different dimensions correspond to sinusoids of different frequencies.

The authors chose sinusoidal encodings because they hypothesized that relative positions could be learned more easily: for a fixed offset, one position's encoding can be represented as a linear function of another's. They also tested learned positional embeddings and found nearly identical performance in their reported ablation. They preferred sinusoidal encodings because these might extrapolate to sequence lengths longer than those seen in training.

## Why self-attention?

The paper compares self-attention, recurrence, and convolution on three criteria:

1. **Per-layer computational complexity**.
2. **Minimum number of sequential operations**, meaning how much parallelization is possible.
3. **Maximum path length** between positions, meaning how many computation steps information must traverse to connect two tokens.

### Complexity and path-length comparison

| Layer type | Per-layer complexity | Sequential operations | Maximum path length |
|---|---:|---:|---:|
| Self-attention | `O(n^2 * d)` | `O(1)` | `O(1)` |
| Recurrent | `O(n * d^2)` | `O(n)` | `O(n)` |
| Convolutional | `O(k * n * d^2)` | `O(1)` | `O(log_k(n))` |
| Restricted self-attention | `O(r * n * d)` | `O(1)` | `O(n/r)` |

Where:

- `n` is sequence length.
- `d` is representation dimensionality.
- `k` is convolution kernel size.
- `r` is neighborhood size in restricted attention.

The comparison explains the paper's architectural choice. Self-attention has quadratic cost in sequence length, but for the sentence lengths and representation sizes common in machine translation, it can be computationally favorable compared with recurrent layers. It also allows every position to connect to every other position in one step.

### Long-range dependency argument

Long-range dependencies are hard for sequence models when information must pass through many computation steps. In RNNs, the path between distant positions grows with sequence length. In convolutional models, distant positions require multiple layers unless the kernel covers the whole sequence. In self-attention, any token can directly attend to any other token in a single layer.

This is one of the paper's deepest ideas: **attention changes the graph topology of sequence modeling**. Instead of forcing information to move through a chain or convolutional hierarchy, the model constructs content-dependent shortcuts between positions.

### Interpretability argument

The authors also note that self-attention can make models more interpretable. Individual attention heads may learn different behaviors, some related to syntactic or semantic sentence structure. This is presented as a side benefit rather than as the primary empirical claim.

## Training setup

### Datasets

The paper evaluates on two machine translation benchmarks:

| Task | Dataset size | Tokenization |
|---|---:|---|
| WMT 2014 English-to-German | About 4.5 million sentence pairs | Byte-pair encoding with shared source-target vocabulary of about 37,000 tokens |
| WMT 2014 English-to-French | About 36 million sentence pairs | Word-piece vocabulary of about 32,000 tokens |

Batches are formed by approximate sequence length. Each batch contains roughly 25,000 source tokens and 25,000 target tokens.

### Hardware and training schedule

The models are trained on one machine with **8 NVIDIA P100 GPUs**.

| Model | Steps | Approx. step time | Approx. training time |
|---|---:|---:|---:|
| Transformer base | 100,000 | 0.4 seconds | 12 hours |
| Transformer big | 300,000 | 1.0 second | 3.5 days |

### Optimizer and learning-rate schedule

The paper uses Adam with:

- `beta_1 = 0.9`
- `beta_2 = 0.98`
- `epsilon = 10^-9`

The learning rate increases linearly during a warmup period and then decays proportionally to inverse square root of the step number:

```text
lrate = d_model^(-0.5) * min(step_num^(-0.5), step_num * warmup_steps^(-1.5))
```

The warmup length is `4000` steps.

### Regularization

The paper uses three main regularization strategies:

1. **Residual dropout** on sublayer outputs before residual addition and layer normalization.
2. **Dropout on embeddings plus positional encodings**.
3. **Label smoothing** with value `epsilon_ls = 0.1`.

Label smoothing makes the model less overconfident. The paper notes it can worsen perplexity while improving accuracy and BLEU.

## Reported results

### Main BLEU results

| Model | EN-DE BLEU | EN-FR BLEU | Notes |
|---|---:|---:|---|
| Transformer base | 27.3 | 38.1 | Base model, much lower training cost than prior competitive systems. |
| Transformer big | 28.4 | 41.0 | New state of the art for EN-DE; new single-model state of the art for EN-FR in the paper's comparison. |

The big Transformer improves the WMT 2014 English-to-German result by more than 2 BLEU over the best previously reported models including ensembles. On English-to-French, it reaches 41.0 BLEU as a single model after 3.5 days on 8 GPUs, at a fraction of the training cost of prior top systems.

### Training-cost comparison

The paper emphasizes that the Transformer is not only better in BLEU but also cheaper to train. In Table 2, the Transformer base model's reported training cost for English-to-German is `3.3 * 10^18` FLOPs, while the Transformer big model's reported cost is `2.3 * 10^19` FLOPs. These costs compare favorably with several prior recurrent or convolutional systems listed in the table.

### Inference setup

For reported results, the authors use checkpoint averaging and beam search:

- Base models: average last 5 checkpoints.
- Big models: average last 20 checkpoints.
- Beam size: 4.
- Length penalty: `alpha = 0.6`.
- Maximum output length: input length + 50, with early termination when possible.

## Ablation and model-variation findings

The paper includes a set of model variations on WMT English-to-German development data. The goal is to identify which architectural choices matter.

### Base configuration

The base model uses:

| Parameter | Value |
|---|---:|
| Encoder/decoder layers `N` | 6 |
| Model dimension `d_model` | 512 |
| Feed-forward dimension `d_ff` | 2048 |
| Attention heads `h` | 8 |
| Key dimension `d_k` | 64 |
| Value dimension `d_v` | 64 |
| Dropout `P_drop` | 0.1 |
| Label smoothing `epsilon_ls` | 0.1 |
| Training steps | 100K |
| Parameters | 65M |

### Big configuration

The big model uses:

| Parameter | Value |
|---|---:|
| Encoder/decoder layers `N` | 6 |
| Model dimension `d_model` | 1024 |
| Feed-forward dimension `d_ff` | 4096 |
| Attention heads `h` | 16 |
| Dropout `P_drop` | 0.3 for English-to-German; 0.1 for English-to-French |
| Training steps | 300K |
| Parameters | 213M |

### Key ablation conclusions

1. **Single-head attention performs worse.** The paper reports that using one attention head is about 0.9 BLEU worse than the best tested setting.
2. **Too many heads can also degrade quality.** Quality drops with excessive head counts when dimensions per head become too small.
3. **Reducing key dimension hurts quality.** The authors interpret this as evidence that determining compatibility between queries and keys is not trivial.
4. **Bigger models perform better.** Increasing model size improves BLEU in the tested setup.
5. **Dropout is important.** Dropout helps avoid overfitting.
6. **Learned positional embeddings perform similarly to sinusoidal encodings.** The authors choose sinusoidal encodings mainly for possible length extrapolation.

## Section-by-section detailed summary

### Abstract

The abstract states the paper's central move: replace recurrent and convolutional sequence transduction architectures with a model based solely on attention. It claims better translation quality, more parallelization, and much shorter training time. The headline results are 28.4 BLEU on WMT 2014 English-to-German and 41.0 BLEU on WMT 2014 English-to-French.

### 1. Introduction

The introduction describes RNNs, LSTMs, and GRUs as the dominant sequence modeling tools at the time. It identifies their sequential nature as a core limitation. Recurrent models generate hidden states step by step, so they cannot parallelize across positions inside a single training example. Attention mechanisms already help with long-distance dependencies, but they are mostly paired with recurrence. The paper proposes using attention itself as the main architecture.

### 2. Background

The background situates the Transformer against convolutional sequence models such as ByteNet and ConvS2S. These models improve parallelism but still require paths whose length grows with token distance, either linearly or logarithmically depending on the convolutional structure. The Transformer reduces that path length to a constant number of operations through self-attention, while using multi-head attention to offset the loss of resolution caused by averaging over attention-weighted positions.

### 3. Model Architecture

This is the technical core. The model is an encoder-decoder stack. The encoder repeatedly applies multi-head self-attention and feed-forward networks. The decoder applies masked self-attention, encoder-decoder attention, and feed-forward networks. Residual connections and layer normalization are used throughout. The section defines scaled dot-product attention, multi-head attention, feed-forward sublayers, embedding sharing, and positional encodings.

### 4. Why Self-Attention

This section provides the architectural rationale. Self-attention has constant sequential depth and constant path length between positions. It can be faster than recurrence when sequence length is smaller than representation dimension, which is often true in machine translation. The paper acknowledges the quadratic sequence-length cost and suggests restricted/local attention for very long inputs as a future efficiency direction.

### 5. Training

The paper gives enough implementation detail to reproduce the training regime: WMT datasets, tokenization, batching by approximate sequence length, P100 hardware, Adam parameters, learning-rate warmup, dropout, and label smoothing. This section also makes clear that training speed is central to the contribution, not an incidental observation.

### 6. Results

The results show that the Transformer beats strong previous systems on WMT 2014 English-to-German and achieves strong English-to-French single-model performance. The table compares BLEU and estimated training FLOPs against ByteNet, GNMT, ConvS2S, MoE, and ensembles. Ablations show the importance of attention heads, dimensionality, model size, dropout, and positional choices.

### 7. Conclusion

The conclusion frames the Transformer as the first sequence transduction model based entirely on attention. It highlights faster training and state-of-the-art translation results. The authors propose applying attention-based models to non-text modalities such as images, audio, and video, investigating restricted attention for large inputs and outputs, and reducing sequentiality in generation.

## Important figures and tables

| Location | Item | Why it matters |
|---|---|---|
| Page 3 | Figure 1: Transformer architecture | Shows the full encoder-decoder design, including embeddings, positional encodings, attention blocks, feed-forward blocks, residual "Add & Norm" blocks, linear projection, and softmax. |
| Page 4 | Figure 2: Scaled dot-product attention and multi-head attention | Visualizes attention as softmax over scaled query-key scores and shows multi-head attention as parallel attention layers whose outputs are concatenated. |
| Page 6 | Table 1: Complexity/path-length comparison | Provides the formal rationale for self-attention over recurrence and convolution. |
| Page 8 | Table 2: BLEU and training cost | Shows the main empirical claim: better translation quality at lower estimated training cost. |
| Page 9 | Table 3: Model variations | Shows which architectural details matter and gives base/big parameter settings. |

## Key technical ideas to retain

### 1. Attention as content-addressed routing

A token representation can dynamically select information from other token positions by comparing a query to keys and taking a weighted combination of values. This is more flexible than fixed local convolution and less sequential than recurrence.

### 2. Multi-head attention as multiple relational channels

Multiple heads let the model attend to different relationships in parallel. Some heads may focus on nearby positions, syntactic relations, alignment patterns, or other task-relevant structures. The paper does not require each head to be hand-designed; it learns the heads jointly.

### 3. Positional encoding as the substitute for recurrence/convolutional order

Removing recurrence and convolution removes built-in position awareness. Positional encodings inject order information while preserving parallel computation.

### 4. Residual + normalization scaffolding is essential

The Transformer is often remembered as "attention only," but the trainable architecture depends on residual connections, layer normalization, feed-forward layers, dropout, and learning-rate scheduling.

### 5. Parallelism is a first-class research objective

The Transformer is motivated not only by accuracy but by hardware efficiency. Its major computations are matrix multiplications over full sequences, enabling parallelization on GPUs.

## Main strengths of the paper

1. **Architectural simplicity at the macro level.** The paper replaces recurrent and convolutional blocks with a uniform attention-based block.
2. **Strong empirical validation.** It reports state-of-the-art or near-state-of-the-art machine translation performance against strong baselines.
3. **Speed and efficiency.** The training-cost comparisons make the result compelling beyond BLEU scores.
4. **Clear theoretical intuition.** The path-length and sequential-operation comparisons explain why self-attention should help long-range dependency learning and parallelization.
5. **Ablation evidence.** The variations table helps distinguish core design choices from incidental ones.
6. **Modularity.** The architecture is easy to scale, adapt, and recompose into later encoder-only, decoder-only, and encoder-decoder systems.

## Limitations and caveats

1. **Quadratic sequence-length cost.** Full self-attention costs `O(n^2 * d)` per layer, which becomes problematic for very long sequences. The paper itself points to restricted/local attention as a future direction.
2. **Empirical scope is machine translation.** The paper's main validation is on WMT translation tasks, not on the full range of tasks later associated with Transformer-based models.
3. **Decoder generation remains autoregressive.** Training is highly parallelizable, but generation still produces output tokens one at a time.
4. **Position handling is external to attention.** The model needs positional encodings because attention alone is permutation-invariant over sequence positions unless position information is added.
5. **Interpretability claims are suggestive.** The paper notes that attention heads may learn syntactic or semantic behaviors, but this is not the central empirical evaluation.

## Conceptual comparison to prior sequence models

### RNN / LSTM / GRU sequence models

- Process tokens sequentially.
- Naturally encode order through recurrence.
- Harder to parallelize across sequence positions.
- Long-range dependencies require information to travel through many recurrent steps.

### Convolutional sequence models

- Parallelize better than recurrence.
- Encode locality naturally.
- Distant tokens require multi-layer paths unless kernels are very large or dilated.

### Transformer self-attention

- Parallel over token positions during training.
- Allows global token-to-token interactions in one layer.
- Requires positional encodings for order.
- Has quadratic cost in sequence length.

## What changed intellectually

The paper reframes sequence modeling from **state propagation** to **setwise relational computation with positional annotations**.

Traditional recurrent models ask: "How should the hidden state evolve as we scan the sequence?"

The Transformer asks: "For each token, which other tokens should it retrieve information from, and through which learned relation heads?"

This shift makes sequence modeling less like reading a sentence left-to-right through a memory state and more like building a fully connected, content-dependent graph over tokens at each layer.

## Practical implementation notes

A faithful base Transformer implementation should include:

- Token embeddings with dimension 512.
- Sinusoidal or learned positional encodings.
- 6 encoder layers and 6 decoder layers.
- 8 attention heads in the base model.
- Scaled dot-product attention.
- Decoder causal masking.
- Encoder-decoder cross-attention.
- Position-wise feed-forward networks with hidden dimension 2048.
- Residual connections around every sublayer.
- Layer normalization after residual addition, as described in the original paper.
- Dropout in residual paths and embedding/positional sums.
- Label smoothing.
- Adam with warmup and inverse-square-root decay.
- Beam search and checkpoint averaging for reported translation results.

## Key numbers

| Item | Number |
|---|---:|
| Base encoder layers | 6 |
| Base decoder layers | 6 |
| Base `d_model` | 512 |
| Base `d_ff` | 2048 |
| Base attention heads | 8 |
| Base `d_k`, `d_v` per head | 64 |
| Base parameters | 65M |
| Big `d_model` | 1024 |
| Big `d_ff` | 4096 |
| Big attention heads | 16 |
| Big parameters | 213M |
| EN-DE training pairs | ~4.5M |
| EN-FR training pairs | ~36M |
| Base training time | ~12 hours on 8 P100 GPUs |
| Big training time | ~3.5 days on 8 P100 GPUs |
| EN-DE BLEU, Transformer base | 27.3 |
| EN-DE BLEU, Transformer big | 28.4 |
| EN-FR BLEU, Transformer big | 41.0 |

## Memex-ready atomic notes

- [[Transformer]] is a sequence transduction architecture based entirely on attention, without recurrent or convolutional layers.
- [[Self-attention]] lets every token position attend to every other token position in the same sequence.
- [[Scaled dot-product attention]] computes `softmax(QK^T / sqrt(d_k))V`.
- [[Multi-head attention]] runs multiple attention operations in parallel over learned projections of queries, keys, and values.
- [[Decoder causal masking]] prevents output positions from attending to future output positions.
- [[Positional encoding]] is necessary because attention without positional information does not encode token order.
- [[Sinusoidal positional encoding]] was chosen partly because it may extrapolate to longer sequence lengths than seen during training.
- [[Residual connections]] and [[layer normalization]] are used around every Transformer sublayer.
- [[Position-wise feed-forward network]] mixes features independently at each token position after attention mixes information across positions.
- [[Self-attention path length]] between any two positions is `O(1)`, while recurrent path length is `O(n)`.
- [[Full self-attention complexity]] is `O(n^2 * d)`, which creates scaling issues for long sequences.
- [[Transformer base]] has 6 encoder layers, 6 decoder layers, `d_model = 512`, 8 heads, and about 65M parameters.
- [[Transformer big]] has `d_model = 1024`, 16 heads, and about 213M parameters.
- [[Attention Is All You Need]] reported 28.4 BLEU on WMT 2014 English-to-German with Transformer big.
- [[Attention Is All You Need]] reported 41.0 BLEU on WMT 2014 English-to-French with Transformer big.
- [[Jakob Uszkoreit]] is credited in the paper with proposing replacement of RNNs by self-attention.
- [[Noam Shazeer]] is credited in the paper with scaled dot-product attention and multi-head attention.
- [[Ashish Vaswani]] and [[Illia Polosukhin]] are credited in the paper with first Transformer model design and implementation.
- [[Tensor2Tensor]] infrastructure was important for accelerating the paper's research iteration.

## Suggested links / backlinks

- [[Attention]]
- [[Self-attention]]
- [[Multi-head attention]]
- [[Scaled dot-product attention]]
- [[Transformer]]
- [[Encoder-decoder architecture]]
- [[Sequence transduction]]
- [[Machine translation]]
- [[BLEU score]]
- [[Positional encoding]]
- [[Autoregressive decoding]]
- [[Layer normalization]]
- [[Residual connections]]
- [[Label smoothing]]
- [[Adam optimizer]]
- [[Tensor2Tensor]]

## Questions this paper answers

1. Can a sequence transduction model perform well without recurrence or convolution?
2. Can self-attention replace RNNs as the main mechanism in encoder-decoder translation models?
3. How can a non-recurrent model represent token order?
4. How does self-attention compare with recurrence and convolution in computational path length?
5. Does multi-head attention improve over single-head attention?
6. Can a more parallel architecture train faster while improving BLEU?

## Questions this paper leaves open

1. How should attention be scaled to very long sequences when full attention is quadratic?
2. Can generation be made less sequential than standard autoregressive decoding?
3. How well does the architecture generalize beyond text and machine translation?
4. How should attention heads be interpreted, and are attention patterns faithful explanations?
5. What is the best positional representation for different modalities and sequence lengths?

## Compact glossary

| Term | Meaning in this paper |
|---|---|
| Sequence transduction | Mapping one sequence to another, such as source sentence to translated sentence. |
| Encoder | Network that maps input tokens to continuous representations. |
| Decoder | Network that generates output tokens autoregressively using previous outputs and encoder representations. |
| Attention | Mechanism that computes weighted sums of values based on query-key compatibility. |
| Self-attention | Attention where queries, keys, and values come from the same sequence. |
| Encoder-decoder attention | Attention where decoder states attend to encoder outputs. |
| Scaled dot-product attention | Dot-product attention divided by `sqrt(d_k)` before softmax. |
| Multi-head attention | Multiple attention operations run in parallel over learned projections. |
| Positional encoding | Vector added to token embeddings to encode token position. |
| Residual connection | Adding a sublayer input back to its output. |
| Layer normalization | Normalization applied around sublayers to stabilize training. |
| Label smoothing | Regularization that softens target labels to reduce overconfidence. |
| BLEU | Automatic metric for machine translation quality. |

## Bottom line

The paper's enduring contribution is the demonstration that a carefully engineered attention-only architecture can outperform recurrent and convolutional sequence models while training far more efficiently. The Transformer succeeds because it combines global content-based token interactions, multiple relation heads, explicit positional information, residual-normalized depth, and hardware-friendly parallel matrix operations.

For memex purposes, the highest-value abstraction is:

> The Transformer turns sequence modeling into repeated rounds of learned, content-addressed information routing among all token positions, with positional encodings preserving order and multi-head attention allowing multiple relationship types to be modeled simultaneously.

