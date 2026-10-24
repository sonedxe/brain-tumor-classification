import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/theme.dart';
import 'data/local/local_db.dart';
import 'data/services/connectivity_service.dart';
import 'data/services/offline_service.dart';
import 'data/services/sync_service.dart';
import 'viewmodels/auth_viewmodel.dart';
import 'viewmodels/detail_viewmodel.dart';
import 'viewmodels/history_viewmodel.dart';
import 'viewmodels/prediction_viewmodel.dart';
import 'viewmodels/stats_viewmodel.dart';
import 'views/app_shell.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final connectivity = ConnectivityService.instance;
  await connectivity.initialize();

  final db = LocalDB();
  await db.init();

  final syncService = SyncService(db: db);
  syncService.attach(connectivity);
  // Si arrancamos online, vaciamos lo que quedó pendiente de la sesión previa.
  await syncService.syncNow();

  runApp(
    BrainTumorApp(
      db: db,
      connectivity: connectivity,
      syncService: syncService,
    ),
  );
}

/// Raiz de la app.
///
/// MVVM: `MultiProvider` inyecta el ViewModel como unico objeto de estado
/// compartido. Las vistas lo consumen con `context.watch` o
/// `context.read`, y ninguna lo instancia por su cuenta.
class BrainTumorApp extends StatelessWidget {
  const BrainTumorApp({
    super.key,
    required this.db,
    required this.connectivity,
    required this.syncService,
  });

  final LocalDB db;
  final ConnectivityService connectivity;
  final SyncService syncService;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<PredictionViewModel>(
          create: (_) => PredictionViewModel(
            offlineService: OfflineService(db: db),
            connectivity: connectivity,
          ),
        ),
        ChangeNotifierProvider<AuthViewModel>(
          create: (_) => AuthViewModel(db: db, connectivity: connectivity)
            ..restoreSession(),
        ),
        ChangeNotifierProvider<HistoryViewModel>(
          create: (_) => HistoryViewModel(db: db, connectivity: connectivity)
            ..load(),
        ),
        ChangeNotifierProvider<StatsViewModel>(
          create: (_) => StatsViewModel()..load(),
        ),
        ChangeNotifierProvider<DetailViewModel>(
          create: (_) => DetailViewModel(),
        ),
      ],
      child: MaterialApp(
        title: 'Clasificacion de tumores cerebrales',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.build(),
        home: const AppShell(),
      ),
    );
  }
}
