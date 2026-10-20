# libopus 1.5.2 (fixed point, decoder only) and opusfile 0.12 (no http),
# shared by Makefile (3DS) and Makefile.host (desktop) so both builds decode
# Opus with the same code. Set TP_DIR to this folder before including; see
# README.md here for where the files come from.

OPUS_CELT := bands celt celt_decoder celt_lpc cwrs entcode entdec entenc kiss_fft \
             laplace mathops mdct modes pitch quant_bands rate vq
OPUS_SILK := CNG LPC_analysis_filter LPC_fit LPC_inv_pred_gain NLSF2A NLSF_decode \
             NLSF_stabilize NLSF_unpack PLC bwexpander bwexpander_32 code_signs dec_API \
             decode_core decode_frame decode_indices decode_parameters decode_pitch \
             decode_pulses decoder_set_fs gain_quant init_decoder lin2log log2lin \
             pitch_est_tables resampler resampler_private_AR2 resampler_private_IIR_FIR \
             resampler_private_down_FIR resampler_private_up2_HQ resampler_rom shell_coder \
             sort stereo_MS_to_LR stereo_decode_pred sum_sqr_shift table_LSF_cos tables_LTP \
             tables_NLSF_CB_NB_MB tables_NLSF_CB_WB tables_gain tables_other tables_pitch_lag \
             tables_pulses_per_block
OPUS_CORE := opus opus_decoder opus_multistream opus_multistream_decoder
OPUSFILE_C := info internal opusfile stream

# paths relative to TP_DIR
OPUS_SRC := $(addprefix opus/celt/,$(addsuffix .c,$(OPUS_CELT))) \
            $(addprefix opus/silk/,$(addsuffix .c,$(OPUS_SILK))) \
            $(addprefix opus/src/,$(addsuffix .c,$(OPUS_CORE)))
OPUSFILE_SRC := $(addprefix opusfile/src/,$(addsuffix .c,$(OPUSFILE_C)))

# Fixed point, no float API, no deep PLC / DRED / OSCE (never defined here),
# scratch arrays on the stack (alloca).
OPUS_DEFS := -DOPUS_BUILD -DFIXED_POINT -DDISABLE_FLOAT_API -DUSE_ALLOCA \
             -DHAVE_LRINTF -DHAVE_LRINT -DPACKAGE_VERSION='"1.5.2"'
OPUS_INCS := -I$(TP_DIR)/opus/include -I$(TP_DIR)/opus/celt -I$(TP_DIR)/opus/silk \
             -I$(TP_DIR)/opus/src -I$(TP_DIR)/opus
OPUSFILE_DEFS := -DOP_FIXED_POINT -DOP_DISABLE_FLOAT_API -DOP_HAVE_LRINTF
OPUSFILE_INCS := -I$(TP_DIR)/opus/include -I$(TP_DIR)/opusfile/include
# for the engine's own code
OPUS_ENGINE_INCS := -I$(TP_DIR)/opus/include -I$(TP_DIR)/opusfile/include

# ARMv5E/ARMv6 inline assembly (multiply-accumulate macros) for the ARM11.
OPUS_ARM_DEFS := -DOPUS_ARM_INLINE_ASM -DOPUS_ARM_INLINE_EDSP -DOPUS_ARM_INLINE_MEDIA
