import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/theme.dart';
import 'data/local/local_db.dart';
import 'data/services/connectivity_service.dart';
import 'data/services/notification_service.dart';
import 'data/services/offline_service.dart';
import 'data/services/sync_service.dart';
import 'viewmodels/auth_viewmodel.dart';
import 'viewmodels/detail_viewmodel.dart';
import 'viewmodels/history_viewmodel.dart';
import 'viewmodels/notification_viewmodel.dart';
import 'viewmodels/prediction_viewmodel.dart';
import 'viewmodels/stats_viewmodel.dart';
import 'views/app_shell.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final connectivity = ConnectivityService.instance;
  await connectivity.initialize();

  final db = LocalDB();
  await db.init();

  final notifications = NotificationService();
  try {
    await notifications.init();
  } on Exception catch (error) {
    debugPrint('Notificaciones no disponibles: $error');
  }

  final syncService = SyncService(db: db);
  syncService.attach(connectivity);
  // Si arrancamos online, vaciamos lo que quedó pendiente de la sesión previa.
  await syncService.syncNow();

  runApp(
    BrainTumorApp(
      db: db,
      connectivity: connectivity,
      syncService: syncService,
      notifications: notifications,
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
    required this.notifications,
  });

  final LocalDB db;
  final ConnectivityService connectivity;
  final SyncService syncService;
  final NotificationService notifications;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<PredictionViewModel>(
          create: (_) => PredictionViewModel(
            offlineService: OfflineService(db: db),
            connectivity: connectivity,
            notifications: notifications,
          ),
        ),
        ChangeNotifierProvider<NotificationViewModel>(
          create: (_) => NotificationViewModel(service: notifications)..load(),
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
