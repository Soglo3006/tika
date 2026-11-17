/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.tika.quality;

import java.io.IOException;
import java.io.InputStream;
import java.io.ObjectInputStream;
import java.net.Socket;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

/**
 * IFT3913 - Tache 3.
 *
 * Exemples pedagogiques isoles pour l'analyse statique.
 * Ces methodes ne sont pas appelees par Tika.
 * Ne pas utiliser dans une application de production.
 */
final class IFT3913SecurityExamples {

    private IFT3913SecurityExamples() {
    }

    // Vulnerabilite 2 : configuration XML non securisee (XXE).
    static DocumentBuilder xmlExample()
            throws ParserConfigurationException {
        DocumentBuilderFactory factory =
                DocumentBuilderFactory.newInstance();
        return factory.newDocumentBuilder();
    }

    // Vulnerabilite 3 : construction dangereuse de SQL.
    static ResultSet sqlExample(Connection connection,
                                String documentName)
            throws SQLException {
        String query = String.format(
                "SELECT * FROM documents WHERE name = '%s'",
                documentName
        );
        return connection.createStatement().executeQuery(query);
    }

    // Vulnerabilite 4 : aleatoire faible pour un jeton.
    static String weakTokenExample() {
        return Double.toString(java.lang.Math.random());
    }

    // Vulnerabilite 5 : deserialisation Java non filtree.
    static Object deserializeExample(InputStream input)
            throws IOException, ClassNotFoundException {
        try (ObjectInputStream stream =
                     new ObjectInputStream(input)) {
            return stream.readObject();
        }
    }

    // Vulnerabilite 6 : socket reseau sans chiffrement.
    static Socket socketExample(String host, int port)
            throws IOException {
        return new Socket(host, port);
    }

    // Vulnerabilite 7 : construction de commande dangereuse.
    static ProcessBuilder commandExample(String command) {
        return new ProcessBuilder(command);
    }
}