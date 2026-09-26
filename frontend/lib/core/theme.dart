import 'package:flutter/material.dart';

/// Tema unico de la app.
///
/// MVVM: los colores viven aqui y no se dispersan por las vistas.
class AppTheme {
  const AppTheme._();

  static const Color primary = Color(0xFF0F4C81);
  static const Color secondary = Color(0xFF2E7DB8);
  static const Color background = Color(0xFFF4F6F9);
  static const Color surface = Colors.white;
  static const Color error = Color(0xFFC0392B);
  static const Color success = Color(0xFF1E8449);
  static const Color onSurface = Color(0xFF1B2631);
  static const Color muted = Color(0xFF5D6D7E);

  static const Map<String, Color> classColors = {
    'glioma': Color(0xFFC0392B),
    'meningioma': Color(0xFF8E44AD),
    'pituitario': Color(0xFFB9770E),
    'no_tumor': Color(0xFF1E8449),
  };

  static ThemeData build() {
    final base = ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primary,
        primary: primary,
        secondary: secondary,
        error: error,
      ),
    );

    return base.copyWith(
      scaffoldBackgroundColor: background,
      appBarTheme: const AppBarTheme(
        backgroundColor: primary,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
      ),
      cardTheme: CardThemeData(
        color: surface,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
        margin: const EdgeInsets.symmetric(vertical: 8),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          minimumSize: const Size.fromHeight(52),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
      textTheme: base.textTheme.apply(
        bodyColor: onSurface,
        displayColor: onSurface,
      ),
    );
  }
}
