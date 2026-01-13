/// Session data model for tracking mood metrics over time
class SessionData {
  final List<MoodSnapshot> snapshots = [];
  final List<GuidedPeriod> guidedPeriods = []; // Track Guided mode periods
  final DateTime startTime;
  DateTime? endTime;
  
  DateTime? _guidedStartTime; // Track current Guided period start

  SessionData() : startTime = DateTime.now();

  /// Add a new mood snapshot
  void addSnapshot({
    required int stressScore,
    required int focusScore,
    required int meditationScore,
    required double breathLength,
  }) {
    snapshots.add(MoodSnapshot(
      timestamp: DateTime.now(),
      stressScore: stressScore,
      focusScore: focusScore,
      meditationScore: meditationScore,
      breathLength: breathLength,
    ));
  }

  /// Called when entering Guided mode
  void startGuidedPeriod() {
    _guidedStartTime = DateTime.now();
  }

  /// Called when leaving Guided mode
  void endGuidedPeriod() {
    if (_guidedStartTime != null) {
      guidedPeriods.add(GuidedPeriod(
        start: _guidedStartTime!,
        end: DateTime.now(),
      ));
      _guidedStartTime = null;
    }
  }

  /// End the session
  void endSession() {
    endTime = DateTime.now();
    // Close any open Guided period
    if (_guidedStartTime != null) {
      endGuidedPeriod();
    }
  }

  /// Get session duration in minutes
  double get durationMinutes {
    final end = endTime ?? DateTime.now();
    return end.difference(startTime).inSeconds / 60.0;
  }

  /// Get average stress score
  double get averageStress {
    if (snapshots.isEmpty) return 0;
    return snapshots.map((s) => s.stressScore).reduce((a, b) => a + b) / snapshots.length;
  }

  /// Get average focus score
  double get averageFocus {
    if (snapshots.isEmpty) return 0;
    return snapshots.map((s) => s.focusScore).reduce((a, b) => a + b) / snapshots.length;
  }

  /// Get average meditation score
  double get averageMeditation {
    if (snapshots.isEmpty) return 0;
    return snapshots.map((s) => s.meditationScore).reduce((a, b) => a + b) / snapshots.length;
  }

  /// Get average breath length
  double get averageBreathLength {
    if (snapshots.isEmpty) return 0;
    return snapshots.map((s) => s.breathLength).reduce((a, b) => a + b) / snapshots.length;
  }

  /// Calculate trend for a metric (positive = improving, negative = worsening)
  /// For stress: decreasing is good (negative trend = improvement)
  /// For focus/meditation: increasing is good (positive trend = improvement)
  double calculateTrend(List<int> values) {
    if (values.length < 2) return 0;
    
    // Compare first third to last third
    final third = values.length ~/ 3;
    if (third == 0) return 0;
    
    final firstThird = values.take(third).reduce((a, b) => a + b) / third;
    final lastThird = values.skip(values.length - third).reduce((a, b) => a + b) / third;
    
    return lastThird - firstThird;
  }

  /// Analyze trajectory pattern for a metric
  /// Returns: 'steady_improve', 'steady_decline', 'improved_then_declined',
  /// 'declined_then_improved', 'peaked_middle', 'dipped_middle', 'fluctuated', 'stable'
  String analyzeTrajectory(List<int> values) {
    if (values.length < 6) return 'stable';
    
    final third = values.length ~/ 3;
    final firstAvg = values.take(third).reduce((a, b) => a + b) / third;
    final middleAvg = values.skip(third).take(third).reduce((a, b) => a + b) / third;
    final lastAvg = values.skip(values.length - third).reduce((a, b) => a + b) / third;
    
    // Calculate variance to detect fluctuation
    final mean = values.reduce((a, b) => a + b) / values.length;
    final variance = values.map((v) => (v - mean) * (v - mean)).reduce((a, b) => a + b) / values.length;
    final stdDev = variance > 0 ? variance : 0.0;
    
    // Thresholds for detecting significant changes
    const threshold = 1.2;
    
    final firstToMiddle = middleAvg - firstAvg;
    final middleToLast = lastAvg - middleAvg;
    final firstToLast = lastAvg - firstAvg;
    
    // High variance = fluctuating
    if (stdDev > 4.0) return 'fluctuated';
    
    // Peaked in middle (went up then down)
    if (firstToMiddle > threshold && middleToLast < -threshold) {
      return 'peaked_middle';
    }
    
    // Dipped in middle (went down then up)
    if (firstToMiddle < -threshold && middleToLast > threshold) {
      return 'dipped_middle';
    }
    
    // Improved then declined
    if (firstToMiddle > threshold * 0.5 && middleToLast < -threshold * 0.5 && 
        firstToMiddle.abs() > 0.8 && middleToLast.abs() > 0.8) {
      return 'improved_then_declined';
    }
    
    // Declined then improved
    if (firstToMiddle < -threshold * 0.5 && middleToLast > threshold * 0.5 &&
        firstToMiddle.abs() > 0.8 && middleToLast.abs() > 0.8) {
      return 'declined_then_improved';
    }
    
    // Steady improvement
    if (firstToLast > threshold) return 'steady_improve';
    
    // Steady decline
    if (firstToLast < -threshold) return 'steady_decline';
    
    return 'stable';
  }

  /// Get stress trend (negative = calming down)
  double get stressTrend => calculateTrend(snapshots.map((s) => s.stressScore).toList());

  /// Get focus trend (positive = improving focus)
  double get focusTrend => calculateTrend(snapshots.map((s) => s.focusScore).toList());

  /// Get meditation trend (positive = deepening meditation)
  double get meditationTrend => calculateTrend(snapshots.map((s) => s.meditationScore).toList());

  /// Get trajectory patterns
  String get stressTrajectory => analyzeTrajectory(snapshots.map((s) => s.stressScore).toList());
  String get focusTrajectory => analyzeTrajectory(snapshots.map((s) => s.focusScore).toList());
  String get meditationTrajectory => analyzeTrajectory(snapshots.map((s) => s.meditationScore).toList());

  /// Get breath length trend (positive = longer breaths)
  double get breathLengthTrend {
    final lengths = snapshots.map((s) => s.breathLength).toList();
    if (lengths.length < 2) return 0;
    final third = lengths.length ~/ 3;
    if (third == 0) return 0;
    final firstThird = lengths.take(third).reduce((a, b) => a + b) / third;
    final lastThird = lengths.skip(lengths.length - third).reduce((a, b) => a + b) / third;
    return lastThird - firstThird;
  }

  /// Generate intelligent summary text with trajectory analysis
  String generateSummary() {
    if (snapshots.isEmpty) {
      return 'No session data recorded yet.';
    }

    final duration = durationMinutes;
    final buffer = StringBuffer();

    // Duration summary
    if (duration < 1) {
      buffer.writeln('This was a brief session of less than a minute.');
    } else if (duration < 5) {
      buffer.writeln('You completed a ${duration.toStringAsFixed(1)} minute session.');
    } else if (duration < 15) {
      buffer.writeln('Great job! You completed a ${duration.toStringAsFixed(0)} minute breathing session.');
    } else {
      buffer.writeln('Excellent! You completed an extended ${duration.toStringAsFixed(0)} minute session.');
    }

    // Stress analysis with trajectory
    buffer.writeln();
    switch (stressTrajectory) {
      case 'steady_improve': // For stress, improving means going DOWN
        buffer.writeln('😌 Your stress levels increased steadily — you may have been processing tension.');
        break;
      case 'steady_decline':
        buffer.writeln('✨ Your stress levels dropped consistently throughout — excellent calming effect.');
        break;
      case 'peaked_middle':
        buffer.writeln('📈 Your stress peaked mid-session, then subsided. This release pattern is healthy.');
        break;
      case 'dipped_middle':
        buffer.writeln('� You found calm mid-session, but stress returned toward the end. Try a gentler finish next time.');
        break;
      case 'improved_then_declined': // stress went up then down = good
        buffer.writeln('😌 Stress rose initially, then melted away as you settled in — a classic relaxation curve.');
        break;
      case 'declined_then_improved': // stress went down then up = less good
        buffer.writeln('📊 You relaxed early but stress crept back. Consider extending sessions to consolidate gains.');
        break;
      case 'fluctuated':
        buffer.writeln('🌊 Your stress levels fluctuated throughout. This is common when processing emotions or with external distractions.');
        break;
      default:
        if (averageStress < -2) {
          buffer.writeln('😌 You maintained low stress throughout — calm and centered.');
        } else if (averageStress > 2) {
          buffer.writeln('📊 Stress levels stayed elevated. Try longer exhales to activate your relaxation response.');
        } else {
          buffer.writeln('📊 Your stress levels remained relatively stable.');
        }
    }

    // Focus analysis with trajectory
    switch (focusTrajectory) {
      case 'steady_improve':
        buffer.writeln('\n🎯 Your focus sharpened as the session progressed — you entered a concentrated state.');
        break;
      case 'steady_decline':
        buffer.writeln('\n💭 Your focus drifted over time — this is natural in longer sessions. Try shorter, more frequent practice.');
        break;
      case 'peaked_middle':
        buffer.writeln('\n🎯 Focus peaked mid-session before tapering. You found your flow, then naturally wound down.');
        break;
      case 'dipped_middle':
        buffer.writeln('\n� Focus dipped mid-session but recovered. Your mind wandered, then you brought it back — that\'s the practice!');
        break;
      case 'improved_then_declined':
        buffer.writeln('\n💭 Focus improved, then waned. This is common — try ending sessions while still sharp to build positive associations.');
        break;
      case 'declined_then_improved':
        buffer.writeln('\n🎯 Focus faltered initially, then you found your groove. Great recovery!');
        break;
      case 'fluctuated':
        buffer.writeln('\n🌊 Your focus fluctuated. Training the mind is like training a muscle — consistency builds stability.');
        break;
      default:
        if (averageFocus > 6) {
          buffer.writeln('\n🎯 You maintained strong focus throughout.');
        }
    }

    // Meditation analysis with trajectory
    switch (meditationTrajectory) {
      case 'steady_improve':
        buffer.writeln('\n🧘 You descended steadily into deeper meditation as the session continued.');
        break;
      case 'steady_decline':
        buffer.writeln('\n🌊 Meditation depth decreased over time. Your breathing may have quickened toward the end.');
        break;
      case 'peaked_middle':
        buffer.writeln('\n🧘 You reached peak meditation depth mid-session — a natural arc of deepening then surfacing.');
        break;
      case 'dipped_middle':
        buffer.writeln('\n🔄 Meditation dipped mid-session but you settled back. Brief disruptions are normal.');
        break;
      case 'improved_then_declined':
        buffer.writeln('\n🧘 You achieved deep meditative states, then began transitioning out. A complete session arc.');
        break;
      case 'declined_then_improved':
        buffer.writeln('\n🧘 After an active start, you found your way into meditation. Patience paid off.');
        break;
      case 'fluctuated':
        buffer.writeln('\n🌊 Meditation depth varied. Slow, rhythmic breathing (10+ second cycles) helps stabilize depth.');
        break;
      default:
        if (averageMeditation > 6) {
          buffer.writeln('\n🧘 You maintained meditative depth throughout the session.');
        }
    }

    // Breath length analysis
    if (breathLengthTrend > 2.0) {
      buffer.writeln('\n🌬️ Your breath cycles lengthened significantly — a sign of deep relaxation.');
    } else if (breathLengthTrend < -2.0) {
      buffer.writeln('\n🌬️ Your breathing quickened toward the end. Consider a more gradual finish.');
    } else if (averageBreathLength > 10) {
      buffer.writeln('\n🌬️ Your average breath cycle was ${averageBreathLength.toStringAsFixed(1)} seconds — an excellent meditative pace.');
    } else if (averageBreathLength > 6) {
      buffer.writeln('\n🌬️ Your average breath cycle was ${averageBreathLength.toStringAsFixed(1)} seconds — a healthy, relaxed rhythm.');
    }

    return buffer.toString().trim();
  }

  /// Generate targeted suggestions based on results
  String generateSuggestions() {
    final buffer = StringBuffer();
    
    // === STRESS REDUCTION STRATEGIES ===
    if (averageStress > 0 || stressTrend > 0 || stressTrajectory == 'declined_then_improved') {
      buffer.writeln('📉 REDUCING STRESS\n');
      
      if (averageStress > 2) {
        buffer.writeln('Your stress stayed elevated. Try these techniques:\n');
        buffer.writeln('• Extended Exhale: Breathe in for 4 counts, out for 8 counts. The long exhale activates your vagus nerve and parasympathetic system.');
        buffer.writeln('• Physiological Sigh: Take two short inhales through your nose, then one long exhale through your mouth. This rapidly reduces CO2 and calms the nervous system.');
      } else if (stressTrend > 0.5) {
        buffer.writeln('Your stress increased during the session. Consider:\n');
        buffer.writeln('• Pre-Session Relaxation: Spend 2-3 minutes with eyes closed before starting. Let your body settle before tracking.');
        buffer.writeln('• Body Scan: Before breathing practice, mentally scan from head to toes, consciously releasing tension in each area.');
      }
      
      if (stressTrajectory == 'declined_then_improved') {
        buffer.writeln('• Session Timing: You relaxed but stress returned. Try 20-30% longer sessions to consolidate relaxation gains.');
      }
      if (stressTrajectory == 'fluctuated') {
        buffer.writeln('• Environment Check: Stress fluctuations often come from external distractions. Try a quieter space or use headphones with white noise.');
      }
      buffer.writeln('');
    }
    
    // === FOCUS IMPROVEMENT STRATEGIES ===
    if (averageFocus < 5 || focusTrend < -0.5 || focusTrajectory == 'improved_then_declined') {
      buffer.writeln('🎯 IMPROVING FOCUS\n');
      
      if (averageFocus < 3) {
        buffer.writeln('Your focus was scattered. Build attention with:\n');
        buffer.writeln('• Breath Counting: Count each exhale from 1 to 10, then restart. If you lose count, simply begin again at 1 — no judgment.');
        buffer.writeln('• Anchor Point: Focus attention on one specific sensation — the cool air entering your nostrils, or the rise of your belly.');
        buffer.writeln('• Shorter Sessions: Start with 3-5 minutes of focused practice. Quality beats quantity for building attention.');
      } else if (averageFocus < 5) {
        buffer.writeln('Your focus was moderate. Sharpen it with:\n');
        buffer.writeln('• Noting Practice: When your mind wanders, silently note "thinking" and return to breath. This builds metacognition.');
        buffer.writeln('• Visual Focus: Keep eyes slightly open, gazing softly at a point on the floor. This maintains alertness.');
      }
      
      if (focusTrajectory == 'improved_then_declined') {
        buffer.writeln('• End Strong: Your focus faded toward the end. Try ending sessions slightly before focus drops — leave on a high note to build positive associations.');
      }
      if (focusTrajectory == 'steady_decline') {
        buffer.writeln('• Movement Breaks: In longer sessions, try subtle movements (wiggling toes, rolling shoulders) every 5 minutes to maintain alertness.');
      }
      if (focusTrajectory == 'fluctuated') {
        buffer.writeln('• Consistent Rhythm: Focus fluctuations often follow breath irregularity. Try using the Guided mode to establish a steady rhythm first.');
      }
      buffer.writeln('');
    }
    
    // === DEEPENING MEDITATION STRATEGIES ===
    if (averageMeditation < 5 || meditationTrajectory == 'steady_decline') {
      buffer.writeln('🧘 DEEPENING MEDITATION\n');
      
      if (averageBreathLength < 6) {
        buffer.writeln('Your breathing was relatively quick. Slow it down:\n');
        buffer.writeln('• 4-7-8 Technique: Inhale 4 counts, hold 7 counts, exhale 8 counts. This naturally lengthens cycles and deepens relaxation.');
        buffer.writeln('• Box Breathing: Equal phases — 4 counts inhale, 4 hold, 4 exhale, 4 hold. Navy SEALs use this for calm under pressure.');
      } else if (averageMeditation < 5) {
        buffer.writeln('You\'re on the cusp of deeper states. Try:\n');
        buffer.writeln('• Resonance Breathing: Aim for exactly 6 breaths per minute (5 seconds in, 5 seconds out). This synchronizes heart rate variability.');
        buffer.writeln('• Progressive Lengthening: Start with comfortable breaths, then add 1 second to each exhale every minute.');
      }
      
      if (meditationTrajectory == 'steady_decline') {
        buffer.writeln('• Gentle Re-Entry: Your meditation shallowed toward the end. Before ending, take 3 extra-slow breaths to consolidate the state.');
      }
      if (meditationTrajectory == 'dipped_middle') {
        buffer.writeln('• Mid-Session Reset: When you notice agitation, try 3 deep sighs before returning to regular rhythm.');
      }
      buffer.writeln('');
    }
    
    // === BREATH OPTIMIZATION ===
    if (averageBreathLength < 5 || breathLengthTrend < -1.5) {
      buffer.writeln('🌬️ BREATH OPTIMIZATION\n');
      
      if (averageBreathLength < 4) {
        buffer.writeln('Your breath cycles were quite short (${averageBreathLength.toStringAsFixed(1)}s). Lengthen gradually:\n');
        buffer.writeln('• Exhale Extension: Keep inhales natural, but consciously extend each exhale by 1-2 seconds.');
        buffer.writeln('• Pause Practice: Add a 2-second pause after each exhale. This naturally slows rhythm without forcing.');
      }
      if (breathLengthTrend < -1.5) {
        buffer.writeln('• Ending Ritual: Your breath quickened toward the end. Finish with 5 deliberately slow breaths to "seal" the practice.');
      }
      buffer.writeln('');
    }
    
    // === POSITIVE REINFORCEMENT & ADVANCEMENT ===
    if (averageStress < -1 || averageFocus > 6 || averageMeditation > 6) {
      buffer.writeln('✨ BUILDING ON SUCCESS\n');
      
      if (averageStress < -2 && averageFocus > 6) {
        buffer.writeln('You achieved calm focus — the sweet spot! To go deeper:\n');
        buffer.writeln('• Extend Duration: Add 5 minutes to your next session. Your nervous system is ready.');
        buffer.writeln('• Reduce Guidance: Try more time in Open mode without LED guidance. Trust your body\'s rhythm.');
      }
      if (averageMeditation > 7) {
        buffer.writeln('You reached deep meditative states. Optimize with:\n');
        buffer.writeln('• Same Time Daily: Practice at the same time each day to strengthen circadian entrainment.');
        buffer.writeln('• Post-Practice Integration: Spend 2-3 minutes in stillness after practice to let states integrate.');
      }
      if (stressTrajectory == 'steady_decline' && focusTrajectory == 'steady_improve') {
        buffer.writeln('• Perfect Trajectory: Your session showed optimal trends. Consider this your baseline technique.');
      }
      buffer.writeln('');
    }
    
    // Fallback if nothing triggered
    if (buffer.isEmpty) {
      buffer.writeln('💡 GENERAL RECOMMENDATIONS\n');
      buffer.writeln('• Consistency: Practice daily, even for just 5 minutes. Frequency beats intensity for building capacity.');
      buffer.writeln('• Experiment: Try different techniques — morning vs evening, eyes open vs closed, sitting vs lying down.');
      buffer.writeln('• Progressive Goals: Start with calm, then add focus, then depth. Master each before combining.');
    }
    
    return buffer.toString().trim();
  }

  /// Generate plain text report for email
  String toEmailText() {
    final buffer = StringBuffer();
    buffer.writeln('BreathSense Session Report');
    buffer.writeln('=' * 30);
    buffer.writeln();
    buffer.writeln('Date: ${startTime.toString().substring(0, 16)}');
    buffer.writeln('Duration: ${durationMinutes.toStringAsFixed(1)} minutes');
    buffer.writeln('Breaths recorded: ${snapshots.length}');
    buffer.writeln();
    buffer.writeln('AVERAGES');
    buffer.writeln('-' * 20);
    buffer.writeln('Stress: ${averageStress.toStringAsFixed(1)} (scale: -5 calm to +5 anxious)');
    buffer.writeln('Focus: ${averageFocus.toStringAsFixed(1)} (scale: 0-10)');
    buffer.writeln('Meditation: ${averageMeditation.toStringAsFixed(1)} (scale: 0-10)');
    buffer.writeln('Breath Length: ${averageBreathLength.toStringAsFixed(1)} seconds');
    buffer.writeln();
    buffer.writeln('SUMMARY');
    buffer.writeln('-' * 20);
    buffer.writeln(generateSummary());
    buffer.writeln();
    buffer.writeln('SUGGESTIONS');
    buffer.writeln('-' * 20);
    buffer.writeln(generateSuggestions());
    buffer.writeln();
    buffer.writeln('—');
    buffer.writeln('Generated by BreathSense');
    return buffer.toString();
  }
}

/// A single snapshot of mood metrics at a point in time
class MoodSnapshot {
  final DateTime timestamp;
  final int stressScore;
  final int focusScore;
  final int meditationScore;
  final double breathLength;

  MoodSnapshot({
    required this.timestamp,
    required this.stressScore,
    required this.focusScore,
    required this.meditationScore,
    required this.breathLength,
  });

  /// Seconds since session start
  double secondsSince(DateTime start) {
    return timestamp.difference(start).inMilliseconds / 1000.0;
  }
}

/// A period of time spent in Guided mode
class GuidedPeriod {
  final DateTime start;
  final DateTime end;

  GuidedPeriod({required this.start, required this.end});

  /// Start time in seconds since session start
  double startSecondsSince(DateTime sessionStart) {
    return start.difference(sessionStart).inMilliseconds / 1000.0;
  }

  /// End time in seconds since session start
  double endSecondsSince(DateTime sessionStart) {
    return end.difference(sessionStart).inMilliseconds / 1000.0;
  }
}
