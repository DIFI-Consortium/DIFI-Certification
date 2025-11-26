import numpy as np
import matplotlib.pyplot as plt

# Simulation params
sps = 4
rc_num_taps = 51
rc_beta = 0.35
SNR_dB = 40

def qpsk_modulate(bits, sps):
    const_points = [-1-1j, -1+1j, 1+1j, 1-1j]
    sym_map = [0, 1, 3, 2]
    symbols = []
    for i in range(0, len(pn11_bits) - 1, 2):
        bit_pair = 2 * pn11_bits[i] + pn11_bits[i+1] # TODO MIGHT BE REVERSED!
        symbols.append(const_points[sym_map[bit_pair]])
        symbols.extend([0j] * (sps - 1)) # create pulse train that will get fed into pulse shaping filter
    return np.array(symbols)

def qpsk_demodulate(samples):
    const_points = [-1-1j, -1+1j, 1+1j, 1-1j]
    sym_map = [0, 1, 3, 2]
    demod_bits = []
    for sym in samples:
        distances = [np.abs(sym - point) for point in const_points]
        closest_point = np.argmin(distances)
        if closest_point == sym_map[0]:
            demod_bits.extend([0,0])
        elif closest_point == sym_map[1]:
            demod_bits.extend([0,1])
        elif closest_point == sym_map[2]:
            demod_bits.extend([1,0])
        elif closest_point == sym_map[3]:
            demod_bits.extend([1,1])
    return demod_bits

def rc_filter(num_taps, beta, sps):
    num_taps = 51
    beta = 0.35
    Ts = sps # Assume sample rate is 1 Hz, so sample period is 1, so *symbol* period is 8
    t = np.arange(num_taps) - (num_taps-1)//2
    h = np.sinc(t/Ts) * np.cos(np.pi*beta*t/Ts) / (1 - (2*beta*t/Ts)**2)
    h /= np.sum(h)  # Normalize filter energy
    return h

def fractional_delay_filter(delay):
    N = 21 # number of taps, keep this odd
    n = np.arange(-(N-1)//2, N//2+1) # -10,-9,...,0,...,9,10
    h = np.sinc(n - delay) # calc filter taps
    h *= np.hamming(N) # window the filter to make sure it decays to 0 on both sides
    h /= np.sum(h) # normalize to get unity gain, we don't want to change the amplitude/power
    return h

# Originally 2047 bits for PN11
pn11_bits = [1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1,0,1,0,1,0,1,0,0,1,0,0,0,0,0,0,0,1,1,0,1,0,0,0,0,0,1,1,1,0,0,1,0,0,0,1,1,0,1,1,1,0,1,0,1,1,1,0,1,0,1,0,0,0,1,0,1,0,0,0,0,1,0,1,0,0,0,1,0,0,1,0,0,0,1,0,1,0,1,1,0,1,0,1,0,0,0,0,1,1,0,0,0,0,1,0,0,1,1,1,1,0,0,1,0,1,1,1,0,0,1,1,1,0,0,1,0,1,1,1,1,0,1,1,1,0,0,1,0,0,1,0,1,0,1,1,1,0,1,1,0,0,0,0,1,0,1,0,1,1,1,0,0,1,0,0,0,0,1,0,1,1,1,0,1,0,0,1,0,0,1,0,1,0,0,1,1,0,1,1,0,0,0,1,1,1,1,0,1,1,1,0,1,1,0,0,1,0,1,0,1,0,1,1,1,1,0,0,0,0,0,0,1,0,0,1,1,0,0,0,0,1,0,1,1,1,1,1,0,0,1,0,0,1,0,0,0,1,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,0,0,1,1,0,0,0,1,1,1,0,1,1,1,1,0,1,1,0,1,0,1,0,0,1,0,1,1,0,0,0,0,1,1,0,0,1,1,1,0,0,1,1,1,1,1,1,0,1,1,1,1,0,0,0,0,1,0,1,0,0,1,1,0,0,1,0,0,0,1,1,1,1,1,1,0,1,0,1,1,0,0,0,0,1,0,0,0,1,1,1,0,0,1,0,1,0,1,1,0,1,1,1,0,0,0,0,1,1,0,1,0,1,1,0,0,1,1,1,0,0,0,1,1,1,1,1,0,1,1,0,1,1,0,0,0,1,0,1,1,0,1,1,1,0,1,0,0,1,1,0,1,0,1,0,0,1,1,1,1,0,0,0,0,1,1,1,0,0,1,1,0,0,1,1,0,1,1,1,1,1,1,1,1,1,0,1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1,0,1,1,0,1,0,0,0,1,0,0,1,1,0,0,1,0,1,0,1,1,1,1,1,1,0,0,0,0,1,0,0,0,0,1,1,0,0,1,0,1,0,0,1,1,1,1,1,0,0,0,1,1,1,0,0,0,1,1,0,1,1,0,1,1,0,1,1,1,0,1,1,0,1,1,0,1,0,1,0,1,1,0,1,1,0,0,0,0,0,1,1,0,1,1,1,0,0,0,1,1,1,0,1,0,1,1,0,1,1,0,1,0,0,0,1,1,0,1,1,0,0,1,0,1,1,1,0,1,1,1,1,0,0,1,0,1,0,1,0,0,1,1,1,0,0,0,0,0,1,1,1,0,1,1,0,0,0,1,1,0,1,0,1,1,1,0,1,1,1,0,0,0,1,0,1,0,1,0,1,1,0,1,0,0,0,0,0,0,1,1,0,0,1,0,0,0,0,1,1,1,1,1,0,1,0,0,1,1,0,0,0,1,0,0,1,1,1,1,1,0,1,0,1,1,1,0,0,0,1,0,0,0,1,0,1,1,0,1,0,1,0,1,0,0,1,1,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,1,1,0,0,0,1,1,0,0,1,1,1,1,0,1,1,1,1,1,1,0,0,1,0,1,0,0,0,0,1,1,1,0,0,0,1,0,0,1,1,0,1,1,0,1,0,1,1,1,1,0,1,1,0,0,0,1,0,0,1,0,1,1,1,0,1,0,1,1,0,0,1,0,1,0,0,0,1,1,1,1,0,0,0,1,0,1,1,0,0,1,1,0,1,0,0,1,1,1,1,1,1,0,0,1,1,1,0,0,0,0,1,1,1,1,0,1,1,0,0,1,1,0,0,1,0,1,1,1,1,1,1,1,1,0,0,1,0,0,0,0,0,0,1,1,1,0,1,0,0,0,0,1,1,0,1,0,0,1,0,0,1,1,1,0,0,1,1,0,1,1,1,0,1,1,1,1,1,0,1,0,1,0,1,0,0,0,1,0,0,0,0,0,0,1,0,1,0,1,0,0,0,0,1,0,0,0,0,0,1,0,0,1,0,1,0,0,0,1,0,1,1,0,0,0,1,0,1,0,0,1,1,1,0,1,0,0,0,1,1,1,0,1,0,0,1,0,1,1,0,1,0,0,1,1,0,0,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1,1,0,0,1,1,0,0,0,1,1,1,1,1,1,1,1,0,1,1,0,0,0,0,0,0,1,0,1,1,1,0,0,0,0,1,0,0,1,0,1,1,0,0,1,0,1,1,0,0,1,1,1,1,0,0,1,1,1,1,1,0,0,1,1,1,1,0,0,0,1,1,1,1,0,0,1,1,0,1,1,0,0,1,1,1,1,1,0,1,1,1,1,1,0,0,0,1,0,1,0,0,0,1,1,0,1,0,0,0,1,0,1,1,1,0,0,1,0,1,0,0,1,0,1,1,1,0,0,0,1,1,0,0,1,0,1,1,0,1,1,1,1,1,0,0,1,1,0,1,0,0,0,1,1,1,1,1,0,0,1,0,1,1,0,0,0,1,1,1,0,0,1,1,1,0,1,1,0,1,1,1,1,0,1,0,1,1,0,1,0,0,1,0,0,0,1,1,0,0,1,1,0,1,0,1,1,1,1,1,1,1,0,0,0,1,0,0,0,0,0,1,1,0,1,0,1,0,0,0,1,1,1,0,0,0,0,1,0,1,1,0,1,1,0,0,1,0,0,1,1,0,1,1,1,1,0,1,1,1,1,0,1,0,0,1,0,1,0,0,1,0,0,1,1,0,0,0,1,1,0,1,1,1,1,1,0,1,1,1,0,1,0,0,0,1,0,1,0,1,0,0,1,0,1,0,0,0,0,0,1,1,0,0,0,1,0,0,0,1,1,1,1,0,1,0,1,0,1,1,0,0,1,0,0,0,0,0,1,1,1,1,0,1,0,0,0,1,1,0,0,1,0,0,1,0,1,1,1,1,1,0,1,1,0,0,1,0,0,0,1,0,1,1,1,1,0,1,0,1,0,0,1,0,0,1,0,0,0,0,1,1,0,1,1,0,1,0,0,1,1,1,0,1,1,0,0,1,1,1,0,1,0,1,1,1,1,1,0,1,0,0,0,1,0,0,0,1,0,0,1,0,1,0,1,0,1,0,1,1,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,1,1,0,1,1,0,0,0,0,1,1,1,0,1,1,1,0,0,1,1,0,1,0,1,0,1,1,1,1,1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,1,0,1,0,1,1,1,1,0,1,0,0,0,0,1,0,0,1,0,0,1,0,0,1,0,1,1,0,1,1,0,1,1,0,0,1,1,0,1,1,0,1,1,1,1,1,1,0,1,1,0,1,0,0,0,0,1,0,1,1,0,0,1,0,0,1,0,0,1,1,1,1,0,1,1,0,1,1,1,0,0,1,0,1,1,0,1,0,1,1,1,0,0,1,1,0,0,0,1,0,1,1,1,1,1,1,0,1,0,0,1,0,0,0,0,1,0,0,1,1,0,1,0,0,1,0,1,1,1,1,0,0,1,1,0,0,1,0,0,1,1,1,1,1,1,1,0,1,1,1,0,0,0,0,0,1,0,1,0,1,1,0,0,0,1,0,0,0,0,1,1,1,0,1,0,1,0,0,1,1,0,1,0,0,0,0,1,1,1,1,0,0,1,0,0,1,1,0,0,1,1,1,0,1,1,1,1,1,1,1,0,1,0,1,0,0,0,0,0,1,0,0,0,0,1,0,0,0,1,0,1,0,0,1,0,1,0,1,0,0,0,1,1,0,0,0,0,0,1,0,1,1,1,1,0,0,0,1,0,0,1,0,0,1,1,0,1,0,1,1,0,1,1,1,1,0,0,0,1,1,0,1,0,0,1,1,0,1,1,1,0,0,1,1,1,1,0,1,0,1,1,1,1,0,0,1,0,0,0,1,0,0,1,1,1,0,1,0,1,0,1,1,1,0,1,0,0,0,0,0,1,0,1,0,0,1,0,0,0,1,0,0,0,1,1,0,1,0,1,0,1,0,1,1,1,0,0,0,0,0,0,0,1,0,1,1,0,0,0,0,0,1,0,0,1,1,1,0,0,0,1,0,1,1,1,0,1,1,0,1,0,0,1,0,1,0,1,1,0,0,1,1,0,0,0,0,1,1,1,1,1,1,1,0,0,1,1,0,0,0,0,0,1,1,1,1,1,1,0,0,0,1,1,0,0,0,0,1,1,0,1,1,1,1,0,0,1,1,1,0,1,0,0,1,1,1,1,0,1,0,0,1,1,1,0,0,1,0,0,1,1,1,0,1,1,1,0,1,1,1,0,1,0,1,0,1,0,1,0]
pn11_bits = pn11_bits[:2046]  # make even length since we're using QPSK

# Create transmit signal
samples = qpsk_modulate(pn11_bits, sps)
template = samples # save for correlation later
h_rc = rc_filter(rc_num_taps, rc_beta, sps)
samples = np.convolve(samples, h_rc) # Filter our signal, in order to apply the pulse shaping

# for testing purposes, apply a known fractional delay
h_delay = fractional_delay_filter(0.123) 
samples = np.convolve(samples, h_delay)

# Add some amount of zeros before and after to simulate timing offset
num_zeros_before = 1500
num_zeros_after = 700
samples = np.concatenate((np.zeros(num_zeros_before), samples, np.zeros(num_zeros_after)))

# AWGN
noise_power = np.var(samples) / 10**(SNR_dB / 10)
n = np.sqrt(noise_power / 2) * (np.random.randn(len(samples)) + 1j * np.random.randn(len(samples)))
samples += n

# Plot PSD
if False:
    PSD = 10*np.log10(np.abs(np.fft.fftshift(np.fft.fft(samples)))**2)
    f = np.linspace(-0.5, 0.5, len(PSD))
    plt.figure(0)
    plt.plot(f, PSD)
    plt.xlabel("Normalized Frequency (cycles/sample)")
    plt.ylabel("Power/Frequency (dB)")
    plt.grid()
    plt.show()

if False:
    plt.plot(samples.real, label="I")
    plt.plot(samples.imag, label="Q")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.grid()
    plt.show()

# Correlate against template
correlation = np.abs(np.correlate(samples, template, mode='valid')) # np.correlate includes the conj()
peak_index = np.argmax(correlation)

if False:
    plt.figure(3)
    plt.plot(correlation)
    plt.xlabel("Lag")
    plt.ylabel("Correlation Magnitude")
    plt.grid()
    plt.show()

# Using max point, and two neighboring points, estimate the integer and fractional delay
y_lower = correlation[peak_index - 1]
y_0 = correlation[peak_index]
y_upper = correlation[peak_index + 1]
frac_delay = (y_upper - y_lower) / (2 * (2 * y_0 - y_lower - y_upper))
total_delay = peak_index + frac_delay
print(f"Estimated delay: {total_delay:.4f} samples (integer: {peak_index}, fractional: {frac_delay:.4f})")

# Correct fractional delay
h_delay_correction = fractional_delay_filter(-1 * frac_delay) 
samples = np.convolve(samples, h_delay_correction)
samples = samples[(len(h_delay_correction)-1)//2:] # remove filter delay

# Extract symbols we care about and decimate
samples = samples[peak_index:] # remove transients at start
samples = samples[:len(pn11_bits) * sps // 2 ] # truncate to original length
samples = samples[0::sps] # decimate down to 1 sample per symbol

if False:
    plt.figure(2)
    plt.plot(samples.real)
    plt.plot(samples.imag)
    plt.xlabel("Symbol Index")
    plt.ylabel("Amplitude")
    plt.legend(["I","Q"])
    plt.grid()
    plt.show()

if False:
    plt.figure(1)
    plt.plot(samples.real[0:100], samples.imag[0:100], '.')
    plt.xlabel("I")
    plt.ylabel("Q")
    plt.grid()
    plt.axis('equal')
    plt.show()

# Demodulate
demod_bits = qpsk_demodulate(samples)

# Compare
num_bit_errors = sum([demod_bits[i] != pn11_bits[i] for i in range(len(pn11_bits))])
print(f"Number of bit errors: {num_bit_errors} out of {len(pn11_bits)} bits, BER: {num_bit_errors/len(pn11_bits):.6f}")
#for i in range(len(pn11_bits)):
#    if demod_bits[i] != pn11_bits[i]:
#        print(f"Bit {i}: transmitted {pn11_bits[i]}, received {demod_bits[i]}")

