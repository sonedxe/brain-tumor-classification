import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/theme.dart';
import 'viewmodels/prediction_viewmodel.dart';
import 'views/home_view.dart';

void main() {
  runApp(const BrainTumorApp());
}

/// Raiz de la app.
///
/// MVVM: `MultiProvider` inyecta el ViewModel como unico objeto de estado
/// compartido. Las vistas lo consumen con `context.watch` o
/// `context.read`, y ninguna lo instancia por su cuenta.
class BrainTumorApp extends StatelessWidget {
  const BrainTumorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider<PredictionViewModel>(
      create: (_) => PredictionViewModel(),
      child: MaterialApp(
        title: 'Clasificacion de tumores cerebrales',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.build(),
        home: const HomeView(),
      ),
    );
  }
}
