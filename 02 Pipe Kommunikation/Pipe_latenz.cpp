#include <chrono>
#include <fstream>
#include <iostream>
#include <algorithm>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>

int main(int argc, char* argv[]) {
    long iterations = 100000;  // Standardwert

    if (argc > 1) {
        iterations = std::stol(argv[1]);
    }

    // Warmup-Iterationen: mindestens 1000 oder 10% der Gesamtiterationen
    long warmup = std::min<long>(1000, iterations / 10);
    long total_child_iterations = warmup + iterations;

    int parent_to_child[2];
    int child_to_parent[2];

    if (pipe(parent_to_child) == -1) {
        perror("pipe parent_to_child");
        return 1;
    }
    if (pipe(child_to_parent) == -1) {
        perror("pipe child_to_parent");
        return 1;
    }

    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return 1;
    }

    const char ping = 'X';
    char buf;

    using clock = std::chrono::high_resolution_clock;
    using ns    = std::chrono::nanoseconds;

    if (pid == 0) {
        // ---------------- Kindprozess ----------------
        close(parent_to_child[1]);  // Kind liest nur
        close(child_to_parent[0]);  // Kind schreibt nur

        // Warmup + eigentliche Messungen
        for (long i = 0; i < total_child_iterations; ++i) {
            ssize_t r = read(parent_to_child[0], &buf, 1);
            if (r != 1) {
                if (r < 0) perror("child read");
                break;
            }
            ssize_t w = write(child_to_parent[1], &buf, 1);
            if (w != 1) {
                if (w < 0) perror("child write");
                break;
            }
        }

        close(parent_to_child[0]);
        close(child_to_parent[1]);
        _exit(0);
    }

    // --------------- Elternprozess ----------------
    close(parent_to_child[0]);
    close(child_to_parent[1]);

    // Warmup-Phase (OHNE Messung/Speicherung)
    std::cout << "Führe Warmup durch (" << warmup << " Iterationen)...\n";
    for (long i = 0; i < warmup; ++i) {
        if (write(parent_to_child[1], &ping, 1) != 1) {
            perror("warmup write");
            goto cleanup;
        }
        if (read(child_to_parent[0], &buf, 1) != 1) {
            perror("warmup read");
            goto cleanup;
        }
    }

    // CSV-Datei öffnen
    {
        std::ofstream csv("pipe_latenz.csv");
        if (!csv.is_open()) {
            std::cerr << "Fehler beim Öffnen der CSV-Datei\n";
            goto cleanup;
        }

        csv << "latenz_ns\n";  // Header der CSV

        std::cout << "Starte Messungen (" << iterations << " Iterationen)...\n";

        // Eigentliche Messungen
        for (long i = 0; i < iterations; ++i) {
            auto t0 = clock::now();

            if (write(parent_to_child[1], &ping, 1) != 1) {
                perror("write");
                break;
            }
            if (read(child_to_parent[0], &buf, 1) != 1) {
                perror("read");
                break;
            }

            auto t1 = clock::now();

            ns diff = std::chrono::duration_cast<ns>(t1 - t0);
            double one_way = diff.count() / 2.0;

            csv << one_way << "\n";
        }

        csv.close();
        std::cout << "Messungen abgeschlossen. Daten in pipe_latenz.csv gespeichert.\n";
    }

cleanup:
    close(parent_to_child[1]);
    close(child_to_parent[0]);

    int status = 0;
    waitpid(pid, &status, 0);

    return 0;
}