import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:share_plus/share_plus.dart';
import '../models/session_data.dart';

/// Session report screen showing mood graphs and analysis
class ReportScreen extends StatelessWidget {
  final SessionData sessionData;

  const ReportScreen({super.key, required this.sessionData});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1A1A2E),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text(
          'Session Report',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.share, color: Colors.white),
            onPressed: () => _shareReport(context),
            tooltip: 'Share Report',
          ),
        ],
      ),
      body: sessionData.snapshots.isEmpty
          ? _buildEmptyState()
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Session overview card
                  _buildOverviewCard(),
                  const SizedBox(height: 20),

                  // Stress graph
                  _buildGraphCard(
                    title: 'Stress Level',
                    subtitle: 'Lower is calmer',
                    data: sessionData.snapshots
                        .map((s) => FlSpot(
                              s.secondsSince(sessionData.startTime),
                              s.stressScore.toDouble(),
                            ))
                        .toList(),
                    minY: -5,
                    maxY: 5,
                    gradientColors: [Colors.red.shade300, Colors.green.shade300],
                    invertGradient: true,
                  ),
                  const SizedBox(height: 16),

                  // Focus graph
                  _buildGraphCard(
                    title: 'Focus Level',
                    subtitle: 'Higher is more focused',
                    data: sessionData.snapshots
                        .map((s) => FlSpot(
                              s.secondsSince(sessionData.startTime),
                              s.focusScore.toDouble(),
                            ))
                        .toList(),
                    minY: 0,
                    maxY: 10,
                    gradientColors: [Colors.grey, Colors.purple.shade300],
                  ),
                  const SizedBox(height: 16),

                  // Meditation graph
                  _buildGraphCard(
                    title: 'Meditation Depth',
                    subtitle: 'Higher is deeper',
                    data: sessionData.snapshots
                        .map((s) => FlSpot(
                              s.secondsSince(sessionData.startTime),
                              s.meditationScore.toDouble(),
                            ))
                        .toList(),
                    minY: 0,
                    maxY: 10,
                    gradientColors: [Colors.grey, Colors.indigo.shade300],
                  ),
                  const SizedBox(height: 16),

                  // Breath length graph
                  _buildGraphCard(
                    title: 'Breath Cycle Length',
                    subtitle: 'Seconds per breath',
                    data: sessionData.snapshots
                        .map((s) => FlSpot(
                              s.secondsSince(sessionData.startTime),
                              s.breathLength,
                            ))
                        .toList(),
                    minY: 0,
                    maxY: 20,
                    gradientColors: [Colors.orange.shade200, Colors.cyan.shade300],
                  ),
                  const SizedBox(height: 24),

                  // Summary text
                  _buildSummaryCard(),
                  const SizedBox(height: 16),

                  // Suggestions card
                  _buildSuggestionsCard(),
                  const SizedBox(height: 24),

                  // Email button
                  _buildEmailButton(context),
                  const SizedBox(height: 32),
                ],
              ),
            ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.timeline, size: 64, color: Colors.grey[600]),
          const SizedBox(height: 16),
          Text(
            'No session data yet',
            style: TextStyle(
              color: Colors.grey[400],
              fontSize: 18,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Complete a breathing session to see your report',
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildOverviewCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            const Color(0xFF2D2D44),
            const Color(0xFF1F1F33),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Session Overview',
                style: TextStyle(
                  color: Colors.grey[300],
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
              Text(
                _formatDate(sessionData.startTime),
                style: TextStyle(
                  color: Colors.grey[500],
                  fontSize: 12,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              _buildStatItem(
                'Duration',
                '${sessionData.durationMinutes.toStringAsFixed(1)} min',
                Icons.timer,
              ),
              const SizedBox(width: 24),
              _buildStatItem(
                'Breaths',
                '${sessionData.snapshots.length}',
                Icons.air,
              ),
              const SizedBox(width: 24),
              _buildStatItem(
                'Avg Length',
                '${sessionData.averageBreathLength.toStringAsFixed(1)}s',
                Icons.waves,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem(String label, String value, IconData icon) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 14, color: Colors.grey[500]),
              const SizedBox(width: 4),
              Text(
                label,
                style: TextStyle(color: Colors.grey[500], fontSize: 11),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGraphCard({
    required String title,
    required String subtitle,
    required List<FlSpot> data,
    required double minY,
    required double maxY,
    required List<Color> gradientColors,
    bool invertGradient = false,
  }) {
    if (data.isEmpty) {
      return const SizedBox.shrink();
    }

    final colors = invertGradient ? gradientColors.reversed.toList() : gradientColors;
    
    // Build range annotations for Guided mode periods
    final guidedAnnotations = sessionData.guidedPeriods.map((period) {
      return VerticalRangeAnnotation(
        x1: period.startSecondsSince(sessionData.startTime),
        x2: period.endSecondsSince(sessionData.startTime),
        color: Colors.purple.withAlpha(40),
      );
    }).toList();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF252538),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              Row(
                children: [
                  if (sessionData.guidedPeriods.isNotEmpty) ...[
                    Container(
                      width: 12,
                      height: 12,
                      decoration: BoxDecoration(
                        color: Colors.purple.withAlpha(80),
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                    const SizedBox(width: 4),
                    Text(
                      'Guided',
                      style: TextStyle(color: Colors.grey[500], fontSize: 10),
                    ),
                    const SizedBox(width: 8),
                  ],
                  Text(
                    subtitle,
                    style: TextStyle(color: Colors.grey[500], fontSize: 12),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 120,
            child: LineChart(
              LineChartData(
                minY: minY,
                maxY: maxY,
                rangeAnnotations: RangeAnnotations(
                  verticalRangeAnnotations: guidedAnnotations,
                ),
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  horizontalInterval: (maxY - minY) / 4,
                  getDrawingHorizontalLine: (value) => FlLine(
                    color: Colors.grey[800]!,
                    strokeWidth: 0.5,
                  ),
                ),
                titlesData: FlTitlesData(
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 28,
                      getTitlesWidget: (value, meta) => Text(
                        value.toInt().toString(),
                        style: TextStyle(color: Colors.grey[600], fontSize: 10),
                      ),
                    ),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                ),
                borderData: FlBorderData(show: false),
                lineBarsData: [
                  LineChartBarData(
                    spots: data,
                    isCurved: true,
                    curveSmoothness: 0.3,
                    gradient: LinearGradient(colors: colors),
                    barWidth: 2,
                    isStrokeCapRound: true,
                    dotData: FlDotData(show: false),
                    belowBarData: BarAreaData(
                      show: true,
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: colors.map((c) => c.withAlpha(51)).toList(),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF252538),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.auto_awesome, color: Colors.amber, size: 20),
              const SizedBox(width: 8),
              const Text(
                'Session Summary',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            sessionData.generateSummary(),
            style: TextStyle(
              color: Colors.grey[300],
              fontSize: 14,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSuggestionsCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            const Color(0xFF1E3A5F),
            const Color(0xFF152238),
          ],
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.lightbulb_outline, color: Colors.cyan, size: 20),
              const SizedBox(width: 8),
              const Text(
                'Suggestions',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            sessionData.generateSuggestions(),
            style: TextStyle(
              color: Colors.grey[300],
              fontSize: 14,
              height: 1.6,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmailButton(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: () => _shareReport(context),
        icon: const Icon(Icons.email_outlined),
        label: const Text('Share Report via Email'),
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF4A6572),
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    );
  }

  void _shareReport(BuildContext context) {
    final text = sessionData.toEmailText();
    SharePlus.instance.share(
      ShareParams(
        text: text,
        subject: 'BreathSense Session Report - ${_formatDate(sessionData.startTime)}',
      ),
    );
  }

  String _formatDate(DateTime date) {
    final months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return '${months[date.month - 1]} ${date.day}, ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
  }
}
